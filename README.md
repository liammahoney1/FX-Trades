# FX-Trades

This repository contains a deliberately rough prototype for investigating failed
or delayed institutional FX trades.

## Prototype

`fx_exception_triage.py` starts from fake client and operations evidence, joins
trade records, classifies exception patterns, separates facts from assumptions,
and surfaces control and entitlement constraints for epic scoping.

The code intentionally contains bugs and questionable assumptions so teams can
practice investigation, prioritization, and review before building production
workflow automation.

## Run

```bash
python3 fx_exception_triage.py
```
