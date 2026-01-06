 Bug Summary

  | #   | Severity | File                             | Issue                                                  |
  |-----|----------|----------------------------------|--------------------------------------------------------|
  | 1   | High     | api_key_repository.py, router.py | datetime.utcnow() deprecated in Python 3.12+           |
  | 2   | High     | service.py:145                   | Timezone comparison bug - may mishandle key expiration |
  | 3   | Low      | api_key_repository.py:28         | Docstring says "Bcrypt" but code uses SHA-256          |
  | 4   | Medium   | auth.py:113                      | Silent failure when Neo4j unavailable                  |
  | 5   | Medium   | ApiKeysView.tsx:47               | useEffect could cause double-fetching                  |
  | 6-7 | Medium   | ApiKeysView.tsx:271,273          | Hardcoded amber colors won't work in dark mode         |

  Critical issues to fix first:
  - Bug #1: Deprecated API will break on Python 3.12+
  - Bug #2: Keys could expire incorrectly based on server timezone

  The full report with fix examples is in the plan file. Should I proceed to fix these bugs?

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Code Review - Bug Report

 Summary

 Review of API Key system (backend + frontend) and SDK. Found 7 bugs and 4 improvements.

 ---
 Critical Bugs

 1. Deprecated datetime.utcnow() (Python 3.12+ warning)

 Files:
 - app/features/api_keys/router.py:118
 - app/repositories/neo4j/api_key_repository.py:36,126,141,186,232,283

 Issue: datetime.utcnow() is deprecated in Python 3.12+. Will raise DeprecationWarning.

 Fix: Replace with datetime.now(timezone.utc)

 # Before
 from datetime import datetime
 now = datetime.utcnow().isoformat() + "Z"

 # After
 from datetime import datetime, timezone
 now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

 ---
 2. Timezone comparison bug in expiration check

 File: app/features/api_keys/service.py:144-146

 exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
 if datetime.now(exp_dt.tzinfo) > exp_dt:

 Issue: If expires_at is stored without timezone info (naive datetime), exp_dt.tzinfo will be None, causing
 datetime.now(None) to return local time instead of UTC. This could incorrectly mark keys as expired/not-expired depending  
 on server timezone.

 Fix:
 from datetime import timezone
 exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
 now = datetime.now(timezone.utc)
 if now > exp_dt:
     return None

 ---
 3. Misleading docstring - says "Bcrypt" but uses SHA-256

 File: app/repositories/neo4j/api_key_repository.py:28

 key_hash: Bcrypt hash of the full secret key  # WRONG - actually SHA-256

 Issue: Code uses SHA-256, not Bcrypt. Misleading for security auditors.

 Fix: Change docstring to "SHA-256 hash of the full secret key"

 ---
 Medium Bugs

 4. Silent auth failure when Neo4j driver unavailable

 File: app/core/auth.py:113-115

 driver = get_driver()
 if not driver:
     return None  # Silent failure!

 Issue: If Neo4j is down, API key auth silently fails (returns None), then raises generic 401 "Invalid API key". User can't 
  tell if their key is wrong vs server issue.

 Fix: Add logging for debugging:
 if not driver:
     import logging
     logging.warning("Neo4j driver unavailable for API key validation")
     return None

 ---
 5. Frontend useEffect runs on every callback change

 File: frontend/src/components/apiKeys/ApiKeysView.tsx:47-50

 React.useEffect(() => {
   onRefresh();
   onRefreshUsage();
 }, [onRefresh, onRefreshUsage]);

 Issue: Fetches data whenever callback references change. While parent memoizes these, it's fragile and could cause
 double-fetching if dependencies change.

 Fix: Use a ref to ensure single load:
 const initialLoadRef = React.useRef(false);
 React.useEffect(() => {
   if (!initialLoadRef.current) {
     initialLoadRef.current = true;
     onRefresh();
     onRefreshUsage();
   }
 }, [onRefresh, onRefreshUsage]);

 ---
 6. Hardcoded warning colors don't support dark mode

 File: frontend/src/components/apiKeys/ApiKeysView.tsx:271

 <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">

 Issue: Amber colors won't look good in dark mode.

 Fix: Add dark mode variants:
 <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg">

 ---
 7. Warning text color missing dark mode support

 File: frontend/src/components/apiKeys/ApiKeysView.tsx:273

 <div className="text-amber-600 text-sm">

 Fix:
 <div className="text-amber-600 dark:text-amber-400 text-sm">

 ---
 Improvements (Not Bugs)

 1. SDK base URL doesn't exist yet

 File: sdk/src/amemo/_base_client.py:23

 base_url: str = "https://api.amemo.ai"

 Suggestion: Document that this is placeholder, or default to AMEMO_BASE_URL env var.

 ---
 2. No rate limiting on API key creation

 File: app/features/api_keys/router.py

 Suggestion: Add rate limiting to prevent key creation abuse (e.g., max 10 keys per user).

 ---
 3. SDK headers set once at client creation

 File: sdk/src/amemo/client.py:72-75

 Note: If user changes config.api_key after client creation, changes won't take effect. This is expected but should be      
 documented.

 ---
 4. Type exports might be missing from barrel file

 Check: Verify frontend/src/api/index.ts exports all apiKeys types.

 ---
 Files to Modify

 | File                                            | Priority | Changes                                              |      
 |-------------------------------------------------|----------|------------------------------------------------------|      
 | app/features/api_keys/service.py                | High     | Fix timezone comparison (Bug #2)                     |      
 | app/features/api_keys/router.py                 | High     | Fix deprecated datetime (Bug #1)                     |      
 | app/repositories/neo4j/api_key_repository.py    | High     | Fix deprecated datetime (Bug #1), docstring (Bug #3) |      
 | app/core/auth.py                                | Medium   | Add logging for driver unavailable (Bug #4)          |      
 | frontend/src/components/apiKeys/ApiKeysView.tsx | Medium   | Fix useEffect (Bug #5), dark mode (Bug #6, #7)       |      

 ---
 Fix Priority

 1. High: Bug #1 (deprecated API - will break on Python 3.12+), Bug #2 (timezone - incorrect expiration)
 2. Medium: Bug #4 (debugging), Bug #5 (double-fetch), Bug #6-7 (dark mode)
 3. Low: Bug #3 (docstring accuracy)