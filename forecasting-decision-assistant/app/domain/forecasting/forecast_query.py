class ForecastQuery:
    def __init__(
        self,
        intent,
        product_id=None,
        product_name=None,
        horizon=None,
        customer_code=None,
    ):
        self.intent = intent
        self.product_id = product_id
        self.product_name = product_name
        self.horizon = horizon
        self.customer_code = customer_code
