# Incremental integration

The project already integrates the SDK when the target links `LBLelinkKit` or calls `authWithAppid:secretKey:error:`.

- Keep the existing SDK copy unless the user asks to upgrade. `obtain_sdk.py --check` shows the installed version.
- Keep the existing credential source; do not run onboarding, print, or migrate values.
- Run `integrate_sdk.rb --check`; apply it only if it lists missing items (for example an older integration with `NSAllowsLocalNetworking` instead of `NSAllowsArbitraryLoads`).
- Extend the existing coordinator instead of creating a second browser or connection. A second `LBLelinkConnection` disconnects the first in the free edition.
- If the existing SDK version starts with 3 (regular SDK), the free-edition error codes, install guide, and `queryCastCapability` may be missing; tell the user before relying on them.
