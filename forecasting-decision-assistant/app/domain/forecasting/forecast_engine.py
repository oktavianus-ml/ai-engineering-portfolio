from abc import ABC, abstractmethod
import pandas as pd


class ForecastEngine(ABC):
    """
    Base interface for all forecasting engines.
    Domain layer MUST NOT contain any ML or pandas logic.
    """

    @abstractmethod
    def run(self, sales_df: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """
        Execute forecasting.

        Parameters
        ----------
        sales_df : pd.DataFrame
            Must contain at least:
            - move_date
            - qty_sold

        horizon : int
            Number of days to forecast ahead.

        Returns
        -------
        pd.DataFrame
            With columns:
            - forecast_date
            - forecast_qty
        """
        raise NotImplementedError
