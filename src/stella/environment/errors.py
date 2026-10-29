class EnvironmentDataError(Exception):
    pass


class WeatherUnavailableError(EnvironmentDataError):
    pass
