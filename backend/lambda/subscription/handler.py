# NOTE: Subscription logic (subscribe, unsubscribe, get subscriptions) is
# handled by the music Lambda function in backend/lambda/music/handler.py
# under the /subscribe (POST), /unsubscribe (DELETE), and /subscriptions (GET)
# routes. A dedicated subscription Lambda was not created separately because
# all music and subscription operations share the same DynamoDB tables and
# are cleanly grouped in one function to reduce cold-start overhead and
# simplify API Gateway routing.
#
# Routes handled in music/handler.py:
#   GET    /music           — query/scan music table
#   GET    /subscriptions   — get user subscriptions from subscriptions table
#   POST   /subscribe       — add a subscription to subscriptions table
#   DELETE /unsubscribe     — remove a subscription from subscriptions table
