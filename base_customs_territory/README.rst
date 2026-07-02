======================
Base Customs Territory
======================

Some states or regions belong politically to a country that is part of a
customs union (e.g. the EU), but are themselves excluded from that customs
territory. Examples include the Canary Islands, Ceuta and Melilla (Spain).
Shipments to these regions require customs export documentation just like
shipments to third countries, even though the destination country itself is
a member of the customs union.

This module adds an ``outside_customs_territory`` boolean field to
``res.country.state`` and pre-populates it for the known exceptions:

* **Canary Islands** – Las Palmas, Santa Cruz de Tenerife
* **Ceuta**
* **Melilla**

The flag is admin-editable on the state record, so future exceptions can be
activated without any code change.

Carrier integrations can use this flag to override country-group-based
decisions.