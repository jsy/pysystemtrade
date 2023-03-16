import pandas as pd

from sysbrokers.IB.ib_instruments import (
    futuresInstrumentWithIBConfigData,
    NOT_REQUIRED_FOR_IB,
    ibInstrumentConfigData,
)
from syscore.constants import missing_file, missing_instrument
from syscore.fileutils import resolve_path_and_filename_for_package
from syscore.genutils import return_another_value_if_nan
from syslogdiag.log_to_screen import logtoscreen
from syslogdiag.logger import logger
from sysobjects.instruments import futuresInstrument


class IBconfig(pd.DataFrame):
    pass


IB_FUTURES_CONFIG_FILE = resolve_path_and_filename_for_package(
    "sysbrokers.IB.ib_config_futures.csv"
)


def read_ib_config_from_file(log: logger = logtoscreen("")) -> IBconfig:
    try:
        df = pd.read_csv(IB_FUTURES_CONFIG_FILE)
    except BaseException:
        log.warn("Can't read file %s" % IB_FUTURES_CONFIG_FILE)
        return missing_file

    return IBconfig(df)


def get_instrument_object_from_config(
    instrument_code: str, config: IBconfig = None, log: logger = logtoscreen("")
) -> futuresInstrumentWithIBConfigData:

    new_log = log.setup(instrument_code=instrument_code)

    if config is None:
        config = read_ib_config_from_file()

    if config is missing_file:
        new_log.warn(
            "Can't get config for instrument %s as IB configuration file missing"
            % instrument_code
        )
        return missing_instrument

    list_of_instruments = get_instrument_list_from_ib_config(config=config, log=log)
    try:
        assert instrument_code in list_of_instruments
    except:
        new_log.warn("Instrument %s is not in IB configuration file" % instrument_code)
        return missing_instrument

    futures_instrument_with_ib_data = _get_instrument_object_from_valid_config(
        instrument_code=instrument_code, config=config
    )

    return futures_instrument_with_ib_data


def _get_instrument_object_from_valid_config(
    instrument_code: str, config: IBconfig = None
) -> futuresInstrumentWithIBConfigData:

    config_row = config[config.Instrument == instrument_code]
    symbol = config_row.IBSymbol.values[0]
    exchange = config_row.IBExchange.values[0]
    currency = return_another_value_if_nan(
        config_row.IBCurrency.values[0], NOT_REQUIRED_FOR_IB
    )
    ib_multiplier = return_another_value_if_nan(
        config_row.IBMultiplier.values[0], NOT_REQUIRED_FOR_IB
    )
    price_magnifier = return_another_value_if_nan(
        config_row.priceMagnifier.values[0], 1.0
    )
    ignore_weekly = config_row.IgnoreWeekly.values[0]

    # We use the flexibility of futuresInstrument to add additional arguments
    instrument = futuresInstrument(instrument_code)
    ib_data = ibInstrumentConfigData(
        symbol,
        exchange,
        currency=currency,
        ibMultiplier=ib_multiplier,
        priceMagnifier=price_magnifier,
        ignoreWeekly=ignore_weekly,
    )

    futures_instrument_with_ib_data = futuresInstrumentWithIBConfigData(
        instrument, ib_data
    )

    return futures_instrument_with_ib_data


def get_instrument_code_from_broker_code(
    config: IBconfig, ib_code: str, log: logger = logtoscreen("")
) -> str:

    config_row = config[config.IBSymbol == ib_code]
    if len(config_row) == 0:
        msg = "Broker symbol %s not found in configuration file!" % ib_code
        log.critical(msg)
        raise Exception(msg)

    if len(config_row) > 1:
        ## need to resolve with multiplier
        instrument_code = get_instrument_code_from_broker_code_with_multiplier(
            ib_code=ib_code, config=config, log=log
        )
    else:
        instrument_code = config_row.iloc[0].Instrument

    return instrument_code


def get_instrument_code_from_broker_code_with_multiplier(
    config: IBconfig, ib_code: str, log: logger = logtoscreen("")
) -> str:

    # FIXME PATCH
    if ib_code == "EOE":
        return "AEX"
    else:
        msg = (
            "Broker symbol %s appears more than once in configuration file and NOT AEX!!"
            % ib_code
        )
        log.critical(msg)
        raise Exception(msg)
    """
    this code will work but need to get multiplier from somewhere

    config = self._get_ib_config()
    config_rows = config[config.IBSymbol == ib_code]

    config_row = config_rows[config.IBMultiplier == multiplier]
    if len(config_row) > 1:

        msg = (
            "Broker symbol %s appears more than once in configuration file!"
            % ib_code
        )
        self.log.critical(msg)
        raise Exception(msg)

    return config_row.iloc[0].Instrument
    """


def get_instrument_list_from_ib_config(config: IBconfig, log: logger = logtoscreen("")):
    if config is missing_file:
        log.warn("Can't get list of instruments because IB config file missing")
        return []

    instrument_list = list(config.Instrument)

    return instrument_list
