# Santa Monica Activity Browser
This is a replacement browser for the Santa Monica city-run activities reservation website: https://anc.apm.activecommunities.com/santamonicarecreation.
The primary reason for building this site is that one must click into an activity's detail page to see what days of the week it is on.
This is especially annoying when trying to sign up for a child's swim lessons because there will be 10-12 instances of the same lesson on different days and times and each one must individually be clicked into to see when it is!
So this app provides a card browser that contains that information up front and also a calendar view.

This project is also my first time using an AI for anything. I built this with the opencode terminal and Claude Opus 4.5. So far I'm super impressed with the capability of the AI, but the code (although functional) is still quite a bit of a mess. Functionality isn't cleanly separated between modules, URL's and other settings-type stuff is hardcoded everywhere despite the existince of a settings.py file, and Claude seems to treat Python's typing system like a suggestion rather than a requirement (but hey, maybe that's the Pythonic thing to do with type hints anyhow...).

Another observation while working this small project is that Claude always jumps straight to a solution that is code based, even if the right thing to do is ask the user to run some tests first. Once I realized this and started asking things like "what test can I do to inform the next steps" the development process suddenly started going a lot faster.

Overall I got to a working MVP of the activity browser in about 4-5 20 minute sessions with Claude (using Opus 4.5 burns through my 5 hour quota pretty darn fast!).

## Login Flow

The application supports multi-user sessions.  Each visitor gets their own
isolated connection to the upstream ActiveNet API.

### Anonymous Browsing

When a new visitor arrives, the server automatically bootstraps an anonymous
ActiveNet session on their behalf:

1. The server makes a `GET` request to the ActiveNet sign-in page.  This page
   goes through a redirect chain and ultimately returns HTML that embeds a CSRF
   token (`window.__csrfToken = "..."`) in an inline `<script>` tag.
2. The CSRF token and all cookies set during the redirect chain are captured
   and stored in a new `ActiveNetClient` instance.
3. A cryptographically random session ID (generated via `secrets.token_urlsafe`)
   is created and sent to the visitor's browser as an `httponly` cookie
   (`samo_session`).
4. The visitor can now browse and search activities without logging in — the
   bootstrapped session provides the cookies and CSRF token needed for read-only
   API calls.

### Logging In

When a visitor clicks "Log In", they are presented with a form that asks for
their ActiveNet email and password.  On submission:

1. The browser sends the email and password to `POST /login` on this server.
2. The server's route handler receives the credentials as local function
   parameters.
3. The handler calls `ActiveNetClient.login(username, password)`, which builds
   a JSON request body and sends it to the upstream ActiveNet API at
   `POST /rest/user/signin` over HTTPS.
4. The upstream API validates the credentials and, on success, returns new
   session cookies, a JWT access token, a JWT refresh token, and basic customer
   info (name, email, customer ID).
5. The server updates the visitor's `ActiveNetClient` instance with the new
   session cookies and tokens.  It also stores the non-sensitive customer info
   (name, email, customer ID) for display in the UI header.
6. The visitor is redirected to the homepage.  Their session is now
   authenticated and the header shows their name with a "Log Out" link.

### Logging Out

When a visitor clicks "Log Out":

1. The server looks up their session by the `samo_session` cookie.
2. The `ActiveNetClient` instance is cleared (all cookies, tokens, and user
   info are wiped) and removed from the session store.
3. The `samo_session` cookie is deleted from the browser.
4. The visitor is redirected to the homepage.  On the next request, a new
   anonymous session is bootstrapped automatically.

### Session Isolation

Each visitor's `ActiveNetClient` instance is stored in an in-memory dictionary
on the server, keyed by their random session ID.  Different visitors never
share a client instance.  Sessions do not survive a server restart.

### Password Security

The plaintext password is handled with strict discipline to ensure it is never
retained after use:

- **Never stored as an attribute**: The password is only ever present as a
  function parameter — first in the `POST /login` route handler, then in the
  `ActiveNetClient.login()` method.  It is never assigned to `self`, a class
  attribute, a global, or any persistent data structure.
- **Never written to disk**: The password is not saved to any file, database,
  session store, cookie, or cache.
- **Never logged**: The application does not log request bodies.  The `login()`
  method logs the *username* on success or failure for diagnostics, but never
  the password.
- **Single use**: The password appears in exactly one place — the JSON body of
  the HTTPS POST to the upstream ActiveNet API (`/rest/user/signin`).
- **Immediate disposal**: After the upstream API call returns, the `password`
  local variable goes out of scope and becomes eligible for garbage collection.
  No reference to it survives.
- **What IS stored**: Only the upstream API's session tokens (`JSESSIONID`,
  `access_token`, `refresh_token`) and non-sensitive customer info (`first_name`,
  `last_name`, `email`, `customer_id`) are retained in memory for the duration
  of the session.
