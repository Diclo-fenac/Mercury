# Firestore Database Schema
**Generated on**: 2026-01-23T22:51:38.429355
**Project ID**: walmart-happy-spark
**Collections**: 3
**Total Documents**: 46

## Collections Overview

### 📁 users
**Documents**: 20
**Fields**: 41

| Field | Type | Status | Nullable | Notes |
|-------|------|--------|----------|-------|
| created_at | timestamp | required | No |  |
| behavior | map | required | No |  |
| behavior.frequent_categories | array | optional | No |  |
| behavior.most_viewed_products | array | required | No |  |
| preferences | map | required | No |  |
| preferences.budget_range | map | required | No |  |
| preferences.budget_range.min | integer | required | No |  |
| preferences.budget_range.max | integer | required | No |  |
| preferences.preferred_size | array | required | No |  |
| preferences.preferred_colors | array | required | No |  |
| preferences.preferred_brands | array | required | No |  |
| preferences.preferred_categories | array | required | No |  |
| updated_at | timestamp | required | No |  |
| last_activity | timestamp | required | No |  |
| stats | map | required | No |  |
| stats.add_to_cart | integer | required | No |  |
| stats.views | integer | required | No |  |
| stats.purchases | integer | required | No |  |
| stats.searches | integer | optional | No |  |
| name | string | required | No |  |
| id | string | required | No |  |
| gender | string | common | No |  |
| health | array | common | No |  |
| stats.search_appearances | integer | common | No |  |
| stats.reviews_written | integer | common | No |  |
| stats.compare_with_other_products | integer | common | No |  |
| stats.refunds | integer | common | No |  |
| stats.ratings_given | integer | common | No |  |
| stats.hover_events | integer | common | No |  |
| stats.questions_asked | integer | common | No |  |
| stats.shares | integer | common | No |  |
| stats.clicks | integer | common | No |  |
| stats.remove_from_cart | integer | common | No |  |
| stats.wishlist_additions | integer | common | No |  |
| stats.promo_code_used | integer | common | No |  |
| location | map | common | No |  |
| location.lat | number | common | No |  |
| location.address | string | common | No |  |
| location.state | string | common | No |  |
| location.lon | number | common | No |  |
| location.city | string | common | No |  |

### 📁 conversations
**Documents**: 6
**Fields**: 7

| Field | Type | Status | Nullable | Notes |
|-------|------|--------|----------|-------|
| created_at | timestamp | required | No |  |
| title | string | required | No |  |
| user_id | string | required | No |  |
| last_message_at | timestamp | common | No |  |
| updated_at | timestamp | required | No |  |
| message_count | integer | required | No |  |
| id | string | required | No |  |

### 📁 products
**Documents**: 20
**Fields**: 64

| Field | Type | Status | Nullable | Notes |
|-------|------|--------|----------|-------|
| created_at | string | required | No |  |
| description | string | required | No |  |
| tags | map | required | No |  |
| tags.Fit | string | common | No |  |
| tags.Brand Fit | string | optional | No |  |
| tags.Suitable For | string | common | No |  |
| tags.Type | string | common | No |  |
| tags.Brand Color | string | common | No |  |
| tags.Ideal For | string | common | No |  |
| tags.Neck Type | string | optional | No |  |
| tags.Pack of | string | common | No |  |
| tags.Sales Package | string | common | No |  |
| tags.Pattern | string | required | No |  |
| tags.Fabric Care | string | common | No |  |
| tags.Size | string | optional | No |  |
| tags.Sleeve Type | string | optional | No |  |
| tags.Fabric | string | required | No |  |
| tags.Style Code | string | required | No |  |
| tags.Sleeve | string | common | No |  |
| stock | boolean | required | No |  |
| url | string | required | No |  |
| price | map | required | No |  |
| price.selling | number | required | No |  |
| price.actual | number | required | No |  |
| price.discount_percent | number | required | No |  |
| rating | number | required | No |  |
| images | array | required | No |  |
| sub_category | string | required | No |  |
| updated_at | string | required | No |  |
| brand | string | required | No |  |
| uploaded_at | string | required | No |  |
| online_available | boolean | required | No |  |
| price_history | array | required | No |  |
| category | string | required | No |  |
| availability | array | required | No |  |
| title | string | required | No |  |
| pid | string | required | No |  |
| id | string | required | No |  |
| tags.Generic Name | string | common | No |  |
| tags.Color | string | common | No |  |
| tags.Reversible | string | common | No |  |
| tags.Collar | string | optional | No |  |
| tags.Country of Origin | string | common | No |  |
| tags.Other Details | string | optional | No |  |
| tags.Model Name | string | optional | No |  |
| tags.Occasion | string | optional | No |  |
| tags.Hooded | string | optional | No |  |
| tags.Closure | string | optional | No |  |
| tags.Character | string | optional | No |  |
| tags.Neck | string | optional | No |  |
| tags.Pockets | string | optional | No |  |
| tags.Covered in Warranty | string | optional | No |  |
| tags.Warranty Summary | string | optional | No |  |
| tags.Not Covered in Warranty | string | optional | No |  |
| tags.Domestic Warranty | string | optional | No |  |
| tags.Secondary Color | string | optional | No |  |
| tags.Warranty Service Type | string | optional | No |  |
| tags.Sole Material | string | optional | No |  |
| tags.Care Instructions | string | optional | No |  |
| tags.Weight | string | optional | No |  |
| tags.Outer Material | string | optional | No |  |
| tags.Package contains | string | optional | No |  |
| tags.Length Type | string | optional | No |  |
| tags.Number of Contents in Sales Package | string | optional | No |  |

## Relationships

- **conversations.user_id** → **users** (inferred)
- **users.preferences** contains embedded object (observed)
- **users.stats** contains embedded object (observed)
- **users.preferences** contains embedded object (observed)
- **users.stats** contains embedded object (observed)
- **users.preferences** contains embedded object (observed)
- **users.stats** contains embedded object (observed)
- **products.tags** contains embedded object (observed)
- **products.price** contains embedded object (observed)
- **products.tags** contains embedded object (observed)
- **products.price** contains embedded object (observed)
- **products.tags** contains embedded object (observed)
- **products.price** contains embedded object (observed)

## Access Patterns

### users
- **Read Heavy**: Yes
- **Write Heavy**: No
- **Patterns**: get_by_id, query_by_email, update_preferences

### conversations
- **Read Heavy**: No
- **Write Heavy**: No
- **Patterns**: get_by_user_id, get_by_id, create, delete

### products
- **Read Heavy**: Yes
- **Write Heavy**: No
- **Patterns**: search, get_trending, get_by_category, get_by_id

