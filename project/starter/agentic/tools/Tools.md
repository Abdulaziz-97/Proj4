# Tools Documentation

## 1. Knowledge Base Tools

### search_knowledge_base
- **Purpose**: Find relevant KB articles
- **Input**: query (str), tags (optional str)
- **Output**: List of articles with scores
- **Database**: udahub.db -> knowledge table

## 2. Account Management Tools

### lookup_user_account
- **Purpose**: Get comprehensive user info
- **Input**: user_id (str)
- **Output**: User object with subscription, reservations
- **Databases**: cultpass.db (user, subscription, reservation)

### check_subscription_status
- **Purpose**: Detailed subscription information
- **Input**: user_id (str)
- **Output**: Subscription status, tier, quota remaining
- **Database**: cultpass.db -> subscriptions

## 3. Reservation Tools

### get_user_reservations
- **Purpose**: List user's active reservations
- **Input**: user_id (str)
- **Output**: List of reservations with experience details
- **Database**: cultpass.db -> reservations + experiences

### cancel_reservation
- **Purpose**: Cancel a reservation
- **Input**: reservation_id (str)
- **Output**: Success/failure + confirmation
- **Database**: cultpass.db -> update reservation status

## 4. Subscription Management Tools

### update_subscription_status
- **Purpose**: Pause or cancel subscription
- **Input**: subscription_id (str), action ('pause'|'cancel')
- **Output**: Updated subscription object
- **Database**: cultpass.db -> subscriptions