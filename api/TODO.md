1. Rewrite celery transaction code and queuing code for multithreading support
2. Fix all transactions to be atomic
3. Find a new optimal transaction processing time, or rewrite whole transaction logic (with the threading) to remove the processing locks.
4. Fix the transaction processing logic corner cases
5. Write new functions for EFA to control the stock market (Stop trading for a stock)
6. Rewrite the gain/loss percentage logic that is to be shown in app, use another benchmark time for that (last hour/2 hour instead of last trading cycle)
7. Internal Trading/ Pump and Dump fixes (Auto blocking trade if stock price crosses too much from last benchmark time)
