class ForecastKPICalculator:
    def calculate(self, avg_daily_demand, stock, lead_time):
        stock_coverage = stock / avg_daily_demand
        reorder_point = avg_daily_demand * lead_time

        return {
            "avg_daily_demand": round(avg_daily_demand, 1),
            "stock_coverage_days": round(stock_coverage),
            "reorder_point": round(reorder_point),
        }

#avg_daily_demand = mean(qty_sold)
#stock_coverage = current_stock / avg_daily_demand
#ROP = avg_daily_demand × lead_time