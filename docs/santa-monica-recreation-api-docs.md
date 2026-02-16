# Santa Monica Recreation — ActiveNet REST API Documentation

> Extracted from HAR recording of `anc.apm.activecommunities.com` on 2026-02-15.
> Base URL: `https://anc.apm.activecommunities.com/santamonicarecreation/rest`

---

## Common Conventions

### Standard Query Parameters

All endpoints accept these query parameters:

| Parameter    | Type   | Required | Description                          |
|-------------|--------|----------|--------------------------------------|
| `locale`    | string | Yes      | Locale string, e.g. `en-US`         |
| `ui_random` | number | No       | Cache-buster timestamp (epoch ms)    |

### Standard Request Headers

| Header             | Value                                              | Notes                                  |
|--------------------|----------------------------------------------------|----------------------------------------|
| `Content-Type`     | `application/x-www-form-urlencoded;charset=utf-8` (GET) / `application/json;charset=utf-8` (POST) | Varies by method |
| `X-Requested-With` | `XMLHttpRequest`                                   | Required on all API calls              |
| `X-CSRF-Token`     | `<uuid>`                                           | Required on all POST requests          |
| `Cookie`           | Session cookies from login                         | Required; authenticates the session    |
| `Accept`           | `*/*`                                              |                                        |

### Standard Response Envelope

Every response follows this structure:

```json
{
  "headers": {
    "sessionRefreshedOn": "2026-02-15 10:33:12",
    "sessionExtendedCount": 0,
    "response_code": "0000",
    "response_message": "Successful",
    "page_info": {
      "order_by": "",
      "order_option": "ASC",
      "total_page": 1,
      "total_records_per_page": 20,
      "total_records": 0,
      "page_number": 1
    }
  },
  "body": { ... }
}
```

| Response Code | Meaning          |
|--------------|------------------|
| `"0000"`     | Success          |
| `"0001"`     | No results found |

---

## 1 — Authentication & Session

### 1.1 Login Check

Verifies the current session is valid.

| | |
|---|---|
| **Endpoint** | `/rest/common/logincheck` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "result": "successful"
}
```

---

### 1.2 Get Current User (Extended)

Returns the authenticated user's profile summary and session token.

| | |
|---|---|
| **Endpoint** | `/rest/system/loginuserext` |
| **Method** | `GET` |

**Query Parameters:**

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `options` | string | No       | Opaque options object (passed as-is) |

**Response `body`:**

```json
{
  "user": {
    "ext": {
      "cart_count": 0
    },
    "customerid": 349291,
    "firstname": "Faustin",
    "middlename": "",
    "lastname": "Carter",
    "loginname": null,
    "email": "faustin.carter@gmail.com",
    "onlineadmininstructorid": 0,
    "encodedCustomerId": "F28A0C8A0733A5F9",
    "jsessionid": "node01pc06qmjl7tef...",
    "additional_email": "",
    "guardian_email": null
  }
}
```

---

## 2 — Account & Family

### 2.1 Get Account Summary

Returns the logged-in user's account overview including balance, family members, and avatar.

| | |
|---|---|
| **Endpoint** | `/rest/user/account` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "account": {
    "customer_id": 349291,
    "avatar": "http://anprod.active.com/.../downloadPublicPicture.sdi?...",
    "customer_name": "Faustin Carter",
    "birth_date": "1982-03-15",
    "address": "2261 23rd street Santa Monica, CA  90405",
    "account_balance": "$31.00",
    "due_now": "--",
    "family_name": "Carter",
    "view_all_families": false,
    "family_members": [
      {
        "customer_id": 349292,
        "customer_name": "Eleanor Carter",
        "birth_date": "2017-10-23",
        "role_name": "Child",
        "is_hoh": false
      }
    ],
    "member_since": null,
    "evaluated_skills": 0,
    "qrcode": "<base64 PNG>"
  }
}
```

---

### 2.2 Get Family Members

Returns all family members associated with the account. Used for participant selection during enrollment.

| | |
|---|---|
| **Endpoint** | `/rest/user/family-members` |
| **Method** | `GET` |

**Query Parameters:**

| Parameter        | Type   | Required | Description                   |
|-----------------|--------|----------|-------------------------------|
| `include_retired`| string | No       | Include retired members (empty = no) |

**Response `body`:** Array of family member objects.

```json
[
  {
    "customer_title": "",
    "first_name": "Eleanor",
    "last_name": "Carter",
    "middle_name": "",
    "email": "",
    "gender": "Female",
    "birth_date": "2017-10-23 00:00:00",
    "age_category": "--",
    "customer_id": 349292,
    "disabled": false,
    "photo_key": null,
    "disabled_reasons": [],
    "redirect_url": null
  }
]
```

---

### 2.3 Get Wishlist Family Members

Returns family members eligible for wishlist activities.

| | |
|---|---|
| **Endpoint** | `/rest/user/wishlist-family-members` |
| **Method** | `GET` |

**Response `body`:** Same array schema as [2.2 Get Family Members](#22-get-family-members).

---

### 2.4 My Account Configuration

Returns the configuration/feature toggles for the My Account page.

| | |
|---|---|
| **Endpoint** | `/rest/myaccount/configuration` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "configuration": {
    "payment_and_order_management": {
      "header_label": "Payment and Order Management",
      "options": [
        {
          "name": "redesign_on_cui_my_account_auto_payment_info",
          "label": "Change Auto-Charge Payments",
          "link_url": "https://apm.activecommunities.com/.../autoPaymentPlanSetupOnline.sdi",
          "include": false,
          "parent_option_name": null,
          "is_parent_option": false
        }
      ]
    }
  }
}
```

---

## 3 — Homepage

### 3.1 Get Home Page Settings

Returns the hero image, welcome text, and navigation modules for the landing page.

| | |
|---|---|
| **Endpoint** | `/rest/homepage/homesetting` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "introductory": {
    "introPageGraphic": {
      "title": "1 Beach House Banner",
      "url": "https://akamai-anprod.active.com/.../downloadFile.sdi?...",
      "key": null
    },
    "title": "Welcome!",
    "paragraph": "City recreation programs are offered year-round...",
    "introduction_header": "",
    "introduction_footer": "",
    "modules": [
      {
        "module_type": 0,
        "module_name": "Activities",
        "title": "Browse",
        "text": "Click Activities for classes, camps and programs...",
        "image_url": "https://...",
        "link_url": "https://..."
      }
    ]
  }
}
```

---

### 3.2 Get Customer Header/Footer

Returns custom header/footer HTML for a given page.

| | |
|---|---|
| **Endpoint** | `/rest/customerheaderfooter/{page_id}` |
| **Method** | `GET` |

**Path Parameters:**

| Parameter | Type | Description                       |
|-----------|------|-----------------------------------|
| `page_id` | int  | Page identifier (e.g. `1`, `3`)   |

**Response `body`:**

```json
{
  "online_header_footer": {
    "site_id": 0,
    "page_id": 1,
    "header": "",
    "footer": ""
  }
}
```

---

## 4 — Activity Search & Detail

### 4.1 Get Activity Filters

Returns all available filter options (instructors, categories, centers, seasons, etc.) for the activity search UI.

| | |
|---|---|
| **Endpoint** | `/rest/activities/filters` |
| **Method** | `GET` |

**Response `body`:** Contains arrays of filter options. Key fields:

```json
{
  "instructors": [
    { "id": "385", "desc": "Successful Students & Athletes" }
  ],
  "centers": [ ... ],
  "seasons": [ ... ],
  "categories": [ ... ],
  "activity_types": [ ... ],
  "sites": [ ... ],
  "geographic_areas": [ ... ],
  "skills": [ ... ]
}
```

---

### 4.2 Search Activities

Search/list activities with filters and pagination.

| | |
|---|---|
| **Endpoint** | `/rest/activities/list` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "activity_search_pattern": {
    "skills": [],
    "time_after_str": "",
    "days_of_week": null,
    "activity_select_param": 2,
    "center_ids": [],
    "time_before_str": "",
    "open_spots": null,
    "activity_id": null,
    "activity_category_ids": [],
    "date_before": "",
    "min_age": null,
    "date_after": "",
    "activity_type_ids": [],
    "site_ids": [],
    "for_map": false,
    "geographic_area_ids": [],
    "season_ids": [],
    "activity_department_ids": [],
    "activity_other_category_ids": [],
    "child_season_ids": [],
    "activity_keyword": "",
    "instructor_ids": [],
    "max_age": null,
    "custom_price_from": "",
    "custom_price_to": ""
  },
  "activity_transfer_pattern": {}
}
```

| Field                          | Type     | Description                                    |
|-------------------------------|----------|------------------------------------------------|
| `activity_select_param`       | int      | Search mode (`2` = browse all)                 |
| `activity_keyword`            | string   | Free-text search keyword                       |
| `center_ids`                  | int[]    | Filter by center/facility IDs                  |
| `activity_category_ids`       | int[]    | Filter by category IDs                         |
| `activity_type_ids`           | int[]    | Filter by type IDs (classes, camps, etc.)      |
| `season_ids`                  | int[]    | Filter by season IDs                           |
| `instructor_ids`              | int[]    | Filter by instructor IDs                       |
| `site_ids`                    | int[]    | Filter by site IDs                             |
| `geographic_area_ids`         | int[]    | Filter by geographic area IDs                  |
| `days_of_week`                | int[]?   | Filter by day of week                          |
| `time_after_str` / `time_before_str` | string | Time-of-day range filter              |
| `date_after` / `date_before`  | string   | Date range filter                              |
| `min_age` / `max_age`         | int?     | Age range filter                               |
| `open_spots`                  | int?     | Filter by available openings                   |
| `custom_price_from` / `custom_price_to` | string | Price range filter                  |
| `for_map`                     | bool     | Return map-optimized results                   |
| `skills`                      | array    | Filter by skill requirements                   |

**Response `body`:**

Pagination is in `headers.page_info` (`total_page`, `total_records`, `page_number`).

> **Note:** The fields below reflect the actual API response observed on 2026-02-15 and differ significantly from the original documentation. Fields such as `category_name`, `center_name`, `season_name`, `first_date`, `last_date`, `age_range`, `price`, and `spots_available` are **not present** in the list response.

```json
{
  "activity_items": [
    {
      "id": 103620,
      "name": "1Soul of Cali Creative Arts Camp Wk 1",
      "number": "1201.101",
      "desc": "<p>HTML description...</p>",
      "item_type": 1,
      "detail_url": "https://apm.activecommunities.com/santamonicarecreation/Activity_Search/.../103620?locale=en-US",
      "activity_online_start_time": "",
      "only_one_day": false,
      "date_range_start": "2026-03-30",
      "date_range_end": "2026-04-03",
      "date_range": "March 30, 2026 to April 3, 2026",
      "date_range_description": "",
      "location": {
        "href": "",
        "title": "",
        "label": "Marine Park Building",
        "type": 0,
        "unit": ""
      },
      "ages": "5 - 11y 11m ",
      "age_description": "Age at least 5 yrs but less than 11y 11m,",
      "age_min_year": 5,
      "age_min_month": 0,
      "age_min_week": 0,
      "age_max_year": 11,
      "age_max_month": 11,
      "age_max_week": 0,
      "min_grade": null,
      "max_grade": null,
      "total_open": 35,
      "already_enrolled": 5,
      "search_from_price": null,
      "search_from_price_desc": "",
      "fee": {
        "href": "https://apm.activecommunities.com/santamonicarecreation/Activity_Search/.../103620",
        "title": "",
        "label": "View fee details",
        "type": 2,
        "unit": ""
      },
      "action_link": {
        "href": "https://anc.apm.activecommunities.com/santamonicarecreation/activity/search/enroll/103620?locale=en-US",
        "title": "",
        "label": "Enroll Now",
        "type": 3,
        "unit": ""
      },
      "enroll_now": {
        "href": "https://anc.apm.activecommunities.com/santamonicarecreation/activity/search/enroll/103620?wishlist_id=0&locale=en-US",
        "title": "",
        "label": "Enroll Now",
        "type": 3,
        "unit": ""
      },
      "allow_drop_in_reg": false,
      "allow_flexible_class": false,
      "already_enrolled": 5,
      "num_of_sub_activities": 0,
      "sub_activity_ids": null,
      "parent_activity": false,
      "show_new_flag": false,
      "show_wish_list": true,
      "wish_list_id": 0,
      "wish_list_participants": null,
      "enrolled_participants": null,
      "urgent_message": {
        "group_id": 0,
        "status_description": "",
        "no_urgency_status_description": null
      }
    }
  ]
}
```

| Field | Type | Description |
|---|---|---|
| `id` | int | Activity ID |
| `name` | string | Activity name |
| `number` | string | Activity number, e.g. `"1201.101"` |
| `date_range_start` | string | Start date, ISO format `YYYY-MM-DD` |
| `date_range_end` | string | End date, ISO format `YYYY-MM-DD` |
| `date_range` | string | Pre-formatted date range, e.g. `"March 30, 2026 to April 3, 2026"` |
| `location.label` | string | Facility/room name, e.g. `"Marine Park Building"` |
| `ages` | string | Age range display string, e.g. `"5 - 11y 11m"` |
| `age_description` | string | Verbose age description |
| `total_open` | int | Spots still available |
| `already_enrolled` | int | Number of enrolled participants |
| `fee.href` | string | Link to fee details page (no price value is returned) |
| `action_link` | object | Enrollment CTA with `href` and `label` |

---

### 4.3 Get Activity Detail

Returns the full detail for a single activity.

| | |
|---|---|
| **Endpoint** | `/rest/activity/detail/{activity_id}` |
| **Method** | `GET` |

**Path Parameters:**

| Parameter     | Type | Description        |
|--------------|------|--------------------|
| `activity_id` | int  | Activity identifier |

**Response `body`:**

```json
{
  "detail": {
    "activity_id": 103527,
    "activity_name": "Level 6: Tiger Shark Swim Lessons",
    "wish_list_id": 0,
    "show_wish_list": true,
    "season_name": "Spring 2026",
    "term_name": null,
    "category": "Aquatics/Swim - Group Lessons",
    "sub_category": "Essential Resident/Non-Resident",
    "risk_category": null,
    "activity_type": "Classes",
    "activity_number": "3018.112",
    "first_date": "2026-03-03",
    "last_date": "2026-03-26",
    "facilities": [],
    "instructors": [
      {
        "id": 177,
        "first_name": "TBA",
        "last_name": "TBA",
        "is_primary_instructor": true,
        "email": "",
        "bio": "",
        "notes": "",
        "avatar": "",
        "phone": "",
        "available_for_online_pre_booked_lessons": true,
        "show_instructor_online": true,
        "can_be_scheduled": false
      }
    ],
    "online_notes": "<div>HTML notes...</div>"
  }
}
```

---

### 4.4 Get Meeting & Registration Dates

Returns the schedule patterns and registration windows for an activity.

| | |
|---|---|
| **Endpoint** | `/rest/activity/detail/meetingandregistrationdates/{activity_id}` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "meeting_and_registration_dates": {
    "activity_id": 103527,
    "no_meeting_dates": false,
    "user_entered": false,
    "online_activity_date_description": "",
    "current_date": "2026-02-15 23:26:36",
    "additional_dates": [],
    "activity_patterns": [
      {
        "beginning_date": "2026-03-03",
        "ending_date": "2026-03-26",
        "weeks_of_month": "",
        "exception_dates": [],
        "pattern_dates": [
          {
            "weekdays": "Tue, Thu",
            "starting_time": "16:30:00",
            "ending_time": "16:55:00"
          }
        ]
      }
    ],
    "priority_enrollment_datetimes": {
      "first_daytime_internet": null,
      "first_daytime_internet_nonresidents": null,
      "first_daytime_internet_members": null,
      "last_daytime_internet": null,
      "drop_in_first_daytime_internet": null,
      "drop_in_first_daytime_internet_nonresidents": null,
      "drop_in_first_daytime_internet_members": null,
      "drop_in_last_daytime_internet": null,
      "for_drop_in_activity": false
    },
    "local_priority_enrollment_datetimes": {
      "first_daytime_internet": null,
      "first_daytime_internet_nonresidents": null,
      "first_daytime_internet_members": null,
      "last_daytime_internet": null,
      "drop_in_first_daytime_internet": null,
      "drop_in_first_daytime_internet_nonresidents": null,
      "drop_in_first_daytime_internet_members": null,
      "drop_in_last_daytime_internet": null,
      "for_drop_in_activity": false
    },
    "enrollment_datetimes": [
      {
        "first_daytime_internet": "2026-01-28 06:00:00",
        "first_daytime_internet_nonresidents": "2026-02-04 06:00:00",
        "first_daytime_internet_members": null,
        "last_daytime_internet": "2026-03-01 00:00:00",
        "drop_in_first_daytime_internet": null,
        "drop_in_first_daytime_internet_nonresidents": null,
        "drop_in_first_daytime_internet_members": null,
        "drop_in_last_daytime_internet": null,
        "for_drop_in_activity": false
      }
    ]
  }
}
```

---

### 4.5 Get Button Status

Returns the current enrollment action state (enroll, waitlist, closed, etc.) for an activity.

| | |
|---|---|
| **Endpoint** | `/rest/activity/detail/buttonstatus/{activity_id}` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "button_status": {
    "activity_online_start_time": "",
    "action_link": {
      "href": "https://.../enroll/103527?locale=en-US",
      "title": "",
      "label": "Enroll Now",
      "type": 3,
      "unit": ""
    },
    "team_action_links": null,
    "time_remaining": 0,
    "notification": ""
  }
}
```

| `action_link.type` | Meaning          |
|--------------------|------------------|
| `3`                | Enroll Now       |
| (others)           | Waitlist / Closed / etc. |

---

### 4.6 Get Estimated Price

Returns pricing tiers for an activity.

| | |
|---|---|
| **Endpoint** | `/rest/activity/detail/estimateprice/{activity_id}` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "estimateprice": {
    "show_price_info_online": true,
    "estimate_price": "",
    "prices": [
      {
        "list_name": "",
        "activity_name": "Level 6: Tiger Shark Swim Lessons",
        "details": [
          { "price": "$53.00", "description": "Resident" },
          { "price": "$105.00", "description": "Non-resident" }
        ]
      }
    ],
    "registration_type_prices": [],
    "free": false,
    "simple_fee": false,
    "is_package": false
  }
}
```

---

## 5 — Wishlist

### 5.1 Add to Wishlist

Adds an activity to the user's wishlist.

| | |
|---|---|
| **Endpoint** | `/rest/wishlist` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "activity_id": 103527
}
```

**Response `body`:**

```json
{
  "wish_list_id": "310276",
  "success": true
}
```

---

### 5.2 Get Wishlist

Returns the user's current wishlist items.

| | |
|---|---|
| **Endpoint** | `/rest/wishlist` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "wishlist_items": [
    {
      "activity_online_start_time": "",
      "id": 103527,
      "desc": "<div>HTML description...</div>",
      "item_type": 1,
      "detail_url": "https://...",
      "action_link": {
        "href": "https://.../enroll/103527?wishlist_id=310276&locale=en-US",
        "label": "Enroll Now",
        "type": 3,
        "unit": ""
      },
      "enroll_now": { ... },
      "name": "Level 6: Tiger Shark Swim Lessons",
      "season_name": "Spring 2026",
      "wish_list_id": 310276
    }
  ]
}
```

---

## 6 — Activity Enrollment Flow

The enrollment process is a multi-step sequence. The `reno` (registration enrollment number) returned from step 1 is used as a path parameter in subsequent calls.

### 6.1 Initialize Enrollment

Starts the enrollment process for an activity and returns eligible family members.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "activity_id": "103527",
  "transfer_out_transaction_id": 0,
  "reg_type": 0,
  "enroll_from_waitlist": false,
  "waitlist_history_id": ""
}
```

| Field                          | Type   | Description                                 |
|-------------------------------|--------|---------------------------------------------|
| `activity_id`                 | string | Activity to enroll in                       |
| `reg_type`                    | int    | Registration type (`0` = standard)          |
| `enroll_from_waitlist`        | bool   | Whether enrolling from a waitlist           |
| `waitlist_history_id`         | string | Waitlist entry ID (if applicable)           |
| `transfer_out_transaction_id` | int    | Source transaction ID for transfers          |

**Response `body`:**

```json
{
  "enrollment_detail": {
    "activity_id": 103527,
    "activity_name": "Level 6: Tiger Shark Swim Lessons",
    "reno": 1,
    "is_wait_list": false,
    "warning_message": "",
    "family_members": [
      {
        "customer_id": 349291,
        "first_name": "Faustin",
        "last_name": "Carter",
        "is_valid": false,
        "is_default": true,
        "error_message": "Does not meet age qualification.",
        "selected": false
      },
      {
        "customer_id": 349292,
        "first_name": "Eleanor",
        "last_name": "Carter",
        "is_valid": true,
        "is_default": false,
        "error_message": "",
        "selected": false
      }
    ],
    "cart_count": 0,
    "allow_drop_in_reg": false,
    "allow_flexible_class": false
  }
}
```

---

### 6.2 Select Participant

Assigns a family member as the participant and gets the fee summary.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/participant` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "reno": 1,
  "customer_id": 349292,
  "overrides": [],
  "is_edit_transfer": false,
  "transfer_out_transaction_id": 0,
  "waitlist_history_id": ""
}
```

**Response `body`:**

```json
{
  "result": {
    "enrollFromWaitlist": false,
    "warning_message": "",
    "activity_name": "Level 6: Tiger Shark Swim Lessons",
    "error": null,
    "overrides": [],
    "online_inprogress": false,
    "fee_summary": {
      "sub_total": 53.0,
      "tax": 0.0,
      "total": 53.0,
      "details": [
        {
          "fee_id": 337179,
          "qty": 1,
          "description": "Activity Fee",
          "unit_price": 53.0,
          "price": 53.0
        }
      ]
    },
    "schedule_conflicts": [],
    "allow_ignore_schedule_conflict": true,
    "missing_prerequisite_groups": null,
    "contacts": []
  }
}
```

---

### 6.3 Get Enrollment Merchandises

Returns optional merchandise available during enrollment.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/merchandises` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "merchandises": []
}
```

---

### 6.4 Get Enrollment Donations

Returns donation options available during enrollment.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/donation` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "donations": []
}
```

---

### 6.5 Get Enrollment Waivers

Returns any waivers that must be signed for the enrollment.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/waivers` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "waivers": []
}
```

---

### 6.6 Get Authorized Pickups

Returns authorized pickup contacts for a participant.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/pickups/{customer_id}` |
| **Method** | `GET` |

**Path Parameters:**

| Parameter     | Type | Description                   |
|--------------|------|-------------------------------|
| `reno`        | int  | Enrollment registration number |
| `customer_id` | int  | Participant's customer ID      |

**Response `body`:**

```json
{
  "activity_pickups": {
    "enable_authorized_pickups": false,
    "show_authorized_pickups": false,
    "authorized_pickups": [],
    "pickups": []
  }
}
```

---

### 6.7 Get Custom Questions

Returns any custom questions that must be answered during enrollment.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/customquestions` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "participant_note": "",
  "questions": [],
  "transaction_qty": 1,
  "participant_usa_hockey_number": {
    "usah_code": null,
    "position_id": 0,
    "suggested_usah_code": null
  }
}
```

---

### 6.8 Get Fee Additions

Returns available scholarships, activation codes, and additional fee options.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/{reno}/fees/addition` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "addition_info": {
    "activation_codes": [],
    "family_scholarships": [],
    "optional_scholarships": []
  }
}
```

---

### 6.9 Add to Cart

Finalizes the enrollment details and adds the item to the shopping cart.

| | |
|---|---|
| **Endpoint** | `/rest/activity/enrollment/addtocart` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "reno": 1,
  "participant_note": "",
  "question_answers": [],
  "donation_param": [],
  "waivers": [],
  "pickup_customers": [],
  "participant_usa_hockey_number": {
    "usah_code": "",
    "position_id": 1
  },
  "token": "<CSRF/security token string>"
}
```

| Field                          | Type   | Description                          |
|-------------------------------|--------|--------------------------------------|
| `reno`                        | int    | Enrollment registration number       |
| `participant_note`            | string | Optional note for participant        |
| `question_answers`            | array  | Answers to custom questions          |
| `donation_param`              | array  | Selected donation options            |
| `waivers`                     | array  | Signed waivers                       |
| `pickup_customers`            | array  | Authorized pickup contacts           |
| `token`                       | string | Security token for cart submission   |

**Response `body`:** Empty object `{}` on success.

---

## 7 — Shopping Cart & Checkout

### 7.1 Cart Preparation

Initializes the cart view and returns feature flags.

| | |
|---|---|
| **Endpoint** | `/rest/preparation` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "cart_common_info": {
    "show_coupon_section": true
  },
  "success": true
}
```

---

### 7.2 Get Transaction Details

Returns the full cart contents with line items, participants, and pricing.

| | |
|---|---|
| **Endpoint** | `/rest/transaction` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "has_tax_receipt_printed": false,
  "pay_on_account": [],
  "warnings": [],
  "participants": [
    {
      "first_name": "Eleanor",
      "last_name": "Carter",
      "address": "2261 23rd street Santa Monica, CA  90405",
      "home_phone": {
        "calling_code": "",
        "area": "",
        "phone": "4158108758",
        "ext": "",
        "raw_phone_number": ""
      },
      "email": "",
      "participant_id": 349292,
      "is_login_user": false,
      "transactions": [
        {
          "entity_type": "default",
          "amount_include_tax": 53.0,
          "reno": 1,
          "receipt_entry_identity": "1130047407",
          "transaction_id": 0,
          "transaction_type": 0,
          "reg_type": 0,
          "item_id": 103527,
          "item_name": "Level 6: Tiger Shark Swim Lessons",
          "description": "Level 6: Tiger Shark Swim Lessons - 3018.112",
          "amount": 53.0,
          "taxes": 0.0,
          "original_amount": 53.0,
          "transaction_url": "https://..."
        }
      ]
    }
  ]
}
```

---

### 7.3 Get Order Summary

Returns the computed order totals including subtotal, fees, account credits, and amount due.

| | |
|---|---|
| **Endpoint** | `/rest/order/summary` |
| **Method** | `GET` |

**Query Parameters:**

| Parameter | Type   | Required | Description                           |
|-----------|--------|----------|---------------------------------------|
| `from`    | string | No       | Context hint (e.g. `shoppingcart`)    |

**Response `body`:**

```json
{
  "order_summary": {
    "sub_total": 53.0,
    "original_subtotal": 53.0,
    "coupon": 0,
    "taxes": 0.0,
    "processing_fee": 0.65,
    "processing_fee_discount": 0,
    "total_charges": 53.65,
    "payment_from_account": -31.0,
    "payment_plan_deferred": 0,
    "subsidy_amount": 0,
    "due_now": 22.65,
    "gift_card_amount": 0,
    "checkout_valid": false,
    "confirmation_valid": false,
    "cart_count": 1,
    "activenet_asset_id": ["3018.112"],
    "activenet_asset_type": ["Activity enrollment"],
    "activenet_asset_qty": [1],
    "activenet_asset_price": [53.0],
    "immediately_payment": true,
    "is_need_payment": true
  }
}
```

---

### 7.4 Get Cart Waivers

Returns any cart-level waivers that must be agreed to before checkout.

| | |
|---|---|
| **Endpoint** | `/rest/waiver` |
| **Method** | `GET` |

**Response `body`:** Empty `{}` when no waivers are required.

---

### 7.5 Get Coupons

Returns available and applied coupons for the cart.

| | |
|---|---|
| **Endpoint** | `/rest/coupons` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "dc_coupon": {
    "available_coupons": [],
    "applied_coupons": [],
    "express_registration": false
  }
}
```

---

## 8 — Memberships

### 8.1 Get Membership Search Filters

Returns filter options (centers, categories, types) for the membership search page.

| | |
|---|---|
| **Endpoint** | `/rest/membership/search/filters` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "default_search_location_type": 0,
  "membership_search_default_category": -1,
  "centers": [
    {
      "id": 63,
      "name": "1200 N. PCH",
      "geographicAreaId": 0,
      "hasActivities": false,
      "hasMembershipPackages": false
    }
  ]
}
```

---

### 8.2 Search Membership Packages

Search available membership packages with filters.

| | |
|---|---|
| **Endpoint** | `/rest/membership/packages` |
| **Method** | `POST` |

**Request Body:**

```json
{
  "keyword": "",
  "category_ids": [],
  "package_type_ids": [],
  "min_age": null,
  "max_age": null,
  "site_ids": [],
  "center_ids": []
}
```

**Response `body`:**

```json
{
  "package_list": [
    {
      "id": 245,
      "name": "ACBH-Yoga at the Beach House",
      "category_name": "Adult",
      "description": "5 yoga classes",
      "expiration_description": "Expires 2500 day(s) after issue",
      "uses_description": "5 uses",
      "age_description": "18 yrs +",
      "type_description": "Group",
      "option_description": "Group",
      "primary_fee": 110.0,
      "show_price_info_online": false
    }
  ]
}
```

---

### 8.3 Get Current Memberships

Returns the user's existing membership passes and their status.

| | |
|---|---|
| **Endpoint** | `/rest/membership/currentmemberships` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "current_memberships": [
    {
      "id": 188199,
      "public_id": "djNlTjRVc1MrQUY3cmNveVBYSGlMdz09",
      "primary_customer": {
        "customer_id": 349291,
        "first_name": "Faustin",
        "last_name": "Carter",
        "email": "faustin.carter@gmail.com"
      },
      "membership_package": {
        "package_id": 10,
        "description": "20 swims",
        "package_category_id": 1,
        "primary_fee_amount": "68.25",
        "category_name": "Adult",
        "package_name": "SC - Adult Swim Pass"
      },
      "expiry_date": "2025-10-20",
      "membership_status": {
        "code": 7,
        "text": "Expired"
      },
      "max_uses": 20,
      "uses_left": 20,
      "number_of_passes": 20,
      "pass_holders": [
        {
          "customer_id": 349291,
          "first_name": "Faustin",
          "last_name": "Carter",
          "pass_number": "900093312",
          "is_primary_customer": true,
          "is_login_user": true
        }
      ],
      "auto_renewal": false,
      "show_renew_now": true,
      "renew_action_url": "https://.../membershipenroll/10?membership_id=...",
      "allow_cancel_auto_renewal": false
    }
  ]
}
```

---

### 8.4 Get Current Memberships Participant Filters

Returns participant filter list for viewing memberships by family member.

| | |
|---|---|
| **Endpoint** | `/rest/membership/currentmemberships/search/filters` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "participant_list": [
    {
      "customer_id": 349291,
      "first_name": "Faustin",
      "middle_name": "",
      "last_name": "Carter",
      "is_valid": true,
      "is_default": true,
      "error_message": "",
      "selected": false
    }
  ]
}
```

---

## 9 — Facility Reservations

### 9.1 Get Reservation Search Options

Returns event types and centers available for facility reservations.

| | |
|---|---|
| **Endpoint** | `/rest/reservation/resource/searchoptions` |
| **Method** | `GET` |

**Query Parameters:**

| Parameter | Type   | Required | Description                           |
|-----------|--------|----------|---------------------------------------|
| `keyWord` | string | No       | Search keyword (use empty or `undefined`) |

**Response `body`:**

```json
{
  "event_types": [
    { "id": 101, "text": "lap swim" },
    { "id": 5, "text": "Meeting" },
    { "id": 62, "text": "Tennis Reservation Online" },
    { "id": 70, "text": "Tennis with Ball Machine" }
  ],
  "centers": [
    { "id": 39, "text": "Beach" },
    { "id": 2, "text": "Clover Park Sports Facilities" },
    { "id": 57, "text": "Memorial Park Tennis Courts - 1401 Olympic Blvd." }
  ]
}
```

---

### 9.2 Get Facility Groups

Returns the browsable facility group listing for the reservation landing page with images.

| | |
|---|---|
| **Endpoint** | `/rest/reservation/landingpage/facilitygroups` |
| **Method** | `GET` |

**Response `body`:**

```json
{
  "facility_groups": {
    "anotherResourceFlow": false,
    "facility_group_quantity": 21,
    "online_quick_fac_reserve_title": null,
    "online_quick_fac_reserve_text": "",
    "online_quick_fac_reserve_button_text": "Quick Reserve",
    "reservation_landing_facility_groups": [
      {
        "item_id": 1,
        "item_name": "Annenberg Beach House Canopy 9:00AM",
        "item_heading": "Annenberg Beach House Canopy 9:00AM",
        "display_image_id": 1549,
        "display_image_link": "https://akamai-anprod.active.com/.../downloadFile.sdi?...",
        "item_type": "FacilityGroup"
      }
    ]
  }
}
```

---

### 9.3 Get Reservation Event Types

Returns event types available on the landing page. May return `0001` (no results) if not configured.

| | |
|---|---|
| **Endpoint** | `/rest/reservation/landingpage/eventtypes` |
| **Method** | `GET` |

**Response `body`:** Empty `{}` with `response_code: "0001"` when none configured.

---

## Appendix: Endpoint Quick Reference

| # | Method | Endpoint | Section |
|---|--------|----------|---------|
| 1 | GET | `/rest/common/logincheck` | [1.1](#11-login-check) |
| 2 | GET | `/rest/system/loginuserext` | [1.2](#12-get-current-user-extended) |
| 3 | GET | `/rest/user/account` | [2.1](#21-get-account-summary) |
| 4 | GET | `/rest/user/family-members` | [2.2](#22-get-family-members) |
| 5 | GET | `/rest/user/wishlist-family-members` | [2.3](#23-get-wishlist-family-members) |
| 6 | GET | `/rest/myaccount/configuration` | [2.4](#24-my-account-configuration) |
| 7 | GET | `/rest/homepage/homesetting` | [3.1](#31-get-home-page-settings) |
| 8 | GET | `/rest/customerheaderfooter/{page_id}` | [3.2](#32-get-customer-headerfooter) |
| 9 | GET | `/rest/activities/filters` | [4.1](#41-get-activity-filters) |
| 10 | POST | `/rest/activities/list` | [4.2](#42-search-activities) |
| 11 | GET | `/rest/activity/detail/{activity_id}` | [4.3](#43-get-activity-detail) |
| 12 | GET | `/rest/activity/detail/meetingandregistrationdates/{activity_id}` | [4.4](#44-get-meeting--registration-dates) |
| 13 | GET | `/rest/activity/detail/buttonstatus/{activity_id}` | [4.5](#45-get-button-status) |
| 14 | GET | `/rest/activity/detail/estimateprice/{activity_id}` | [4.6](#46-get-estimated-price) |
| 15 | POST | `/rest/wishlist` | [5.1](#51-add-to-wishlist) |
| 16 | GET | `/rest/wishlist` | [5.2](#52-get-wishlist) |
| 17 | POST | `/rest/activity/enrollment` | [6.1](#61-initialize-enrollment) |
| 18 | POST | `/rest/activity/enrollment/participant` | [6.2](#62-select-participant) |
| 19 | GET | `/rest/activity/enrollment/{reno}/merchandises` | [6.3](#63-get-enrollment-merchandises) |
| 20 | GET | `/rest/activity/enrollment/{reno}/donation` | [6.4](#64-get-enrollment-donations) |
| 21 | GET | `/rest/activity/enrollment/{reno}/waivers` | [6.5](#65-get-enrollment-waivers) |
| 22 | GET | `/rest/activity/enrollment/{reno}/pickups/{customer_id}` | [6.6](#66-get-authorized-pickups) |
| 23 | GET | `/rest/activity/enrollment/{reno}/customquestions` | [6.7](#67-get-custom-questions) |
| 24 | GET | `/rest/activity/enrollment/{reno}/fees/addition` | [6.8](#68-get-fee-additions) |
| 25 | POST | `/rest/activity/enrollment/addtocart` | [6.9](#69-add-to-cart) |
| 26 | GET | `/rest/preparation` | [7.1](#71-cart-preparation) |
| 27 | GET | `/rest/transaction` | [7.2](#72-get-transaction-details) |
| 28 | GET | `/rest/order/summary` | [7.3](#73-get-order-summary) |
| 29 | GET | `/rest/waiver` | [7.4](#74-get-cart-waivers) |
| 30 | GET | `/rest/coupons` | [7.5](#75-get-coupons) |
| 31 | GET | `/rest/membership/search/filters` | [8.1](#81-get-membership-search-filters) |
| 32 | POST | `/rest/membership/packages` | [8.2](#82-search-membership-packages) |
| 33 | GET | `/rest/membership/currentmemberships` | [8.3](#83-get-current-memberships) |
| 34 | GET | `/rest/membership/currentmemberships/search/filters` | [8.4](#84-get-current-memberships-participant-filters) |
| 35 | GET | `/rest/reservation/resource/searchoptions` | [9.1](#91-get-reservation-search-options) |
| 36 | GET | `/rest/reservation/landingpage/facilitygroups` | [9.2](#92-get-facility-groups) |
| 37 | GET | `/rest/reservation/landingpage/eventtypes` | [9.3](#93-get-reservation-event-types) |
