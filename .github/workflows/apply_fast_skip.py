#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GKD 1.12.1 "fast skip" timing tweaks.

Target: app/src/main/kotlin/li/songe/gkd/a11y/A11yRuleEngine.kt
Commit: 5a00f844989471458e4cf4601acb3f4710438f9a (v1.12.1)

Usage (from the GKD repo root):
    python apply_fast_skip.py app/src/main/kotlin/li/songe/gkd/a11y/A11yRuleEngine.kt

Every edit is exact-match and must occur exactly once; the script aborts
without writing anything if the source does not match exactly (e.g. after
you upgrade GKD). A .bak copy is created next to the file.
"""

import sys
import shutil

# (description, old, new)
EDITS = [
    (
        "root-node fallback timeout: 500ms -> 150ms",
        """            scope.launch(Dispatchers.IO) {
                delay(500L)
                if (s.isActive) {""",
        """            scope.launch(Dispatchers.IO) {
                delay(150L)
                if (s.isActive) {""",
    ),
    (
        "retry after an empty query: 300ms -> 50ms (2 sites)",
        """        if (t - lastTriggerTime < 3000L || t - appChangeTime < 3000L) {
            scope.launch(actionDispatcher) {
                delay(300)
                startQueryJob()
            }
        } else if (activityRuleFlow.value.hasFeatureAction) {
            scope.launch(actionDispatcher) {
                delay(300)
                startQueryJob(byForced = true)
            }
        }""",
        """        if (t - lastTriggerTime < 3000L || t - appChangeTime < 3000L) {
            scope.launch(actionDispatcher) {
                delay(50)
                startQueryJob()
            }
        } else if (activityRuleFlow.value.hasFeatureAction) {
            scope.launch(actionDispatcher) {
                delay(50)
                startQueryJob(byForced = true)
            }
        }""",
    ),
    (
        "re-query after a successful action: 300ms -> 50ms",
        """                rule.trigger()
                scope.launch(actionDispatcher) {
                    delay(300)
                    startQueryJob()
                }""",
        """                rule.trigger()
                scope.launch(actionDispatcher) {
                    delay(50)
                    startQueryJob()
                }""",
    ),
    (
        "re-query after an appId correction: 300ms -> 50ms",
        """        scope.launch(actionDispatcher) {
            delay(300)
            startQueryJob()
        }
    }""",
        """        scope.launch(actionDispatcher) {
            delay(50)
            startQueryJob()
        }
    }""",
    ),
    (
        "steady-state content-event throttle: 100ms -> 30ms",
        """            if (a11yEvent.time - lastContentEventTime < 100 && a11yEvent.time - appChangeTime > 5000 && a11yEvent.time - lastTriggerTime > 3000) {""",
        """            if (a11yEvent.time - lastContentEventTime < 30 && a11yEvent.time - appChangeTime > 5000 && a11yEvent.time - lastTriggerTime > 3000) {""",
    ),
]


def apply(text, crlf=False):
    for desc, old, new in EDITS:
        o, n = old, new
        if crlf:
            o = o.replace("\n", "\r\n")
            n = n.replace("\n", "\r\n")
        count = text.count(o)
        if count != 1:
            raise SystemExit(
                "ERROR: [%s] matched %d times (expected 1). "
                "Source changed? Aborting, nothing written." % (desc, count)
            )
        text = text.replace(o, n)
        print("ok: %s" % desc)
    return text


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    path = sys.argv[1]
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")
    try:
        new_text = apply(text, crlf=False)
    except SystemExit:
        if "\r\n" not in text:
            raise
        new_text = apply(text, crlf=True)
    shutil.copyfile(path, path + ".bak")
    with open(path, "wb") as f:
        f.write(new_text.encode("utf-8"))
    print("written: %s (backup: %s.bak)" % (path, path))


if __name__ == "__main__":
    main()
