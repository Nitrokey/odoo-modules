===================
IoT Quality Control
===================

This addon lets an IoT device send measurement values (e.g. CPU, RAM,
storage) to Odoo and attaches them to the quality control (``qc.inspection``)
of a Manufacturing Order.

Each key/value pair is posted as a separate note in the chatter of the
inspection of the given Manufacturing Order. It builds on ``iot_input_oca``
(device authentication, per-key inputs, call logging) and
``quality_control_mrp_oca``.

**Table of contents**

.. contents::
   :local:

Configuration
=============

#. Go to IoT > Config > Add a new Device. It shows a configuration URL.
#. Send a POST request with the parameter ``template=Quality Control
   measurements`` to that URL (once; the URL is valid for a single use)::

       curl -X POST -d 'template=Quality Control measurements' <configuration URL>

   This creates the device with these inputs and returns their serials
   and passphrases as JSON:

   * *Multi input* (function ``parse_multi_input``), the entry point of the
     device. Its **serial** and **passphrase** are used for the requests
     described in Usage.
   * one input per measurement key (``cpu``, ``ram``, ``storage``), using the
     function ``post_measurement`` of the model *iot.quality.control*. The
     **address** of the input is the key name sent by the device.

#. To accept more keys, add inputs to the template (IoT > Config >
   Templates) before step 2, or directly to the device afterwards,
   copying an existing one: model ``iot.quality.control``, function
   ``post_measurement``, params ``{"address": "<key>"}``. Keys that are not
   configured as active inputs are rejected.
#. Optional: restrict the notes to the inspection of one QC test by
   creating the system parameter ``iot_quality_control.qc_test_id``
   (Settings > Technical > System Parameters) with the database ID of
   the *qc.test*. Without it, the open inspection of the Manufacturing
   Order is used (the most recent one if there are several).

Usage
=====

The Manufacturing Order must already have a quality inspection. The device
sends all values in one request to ``/iot/<serial>/multi_input`` (the serial
and passphrase of the *Multi input* input). The ID of the Manufacturing
Order (``mo_id``) must be part of every entry::

    curl -X POST https://odoo.example.com/iot/<serial>/multi_input \
      --data-urlencode 'passphrase=<passphrase>' \
      --data-urlencode 'values=[
        {"address": "cpu", "value": "Intel N100", "mo_id": 42},
        {"address": "ram", "value": "16 GB", "mo_id": 42},
        {"address": "storage", "value": "512 GB", "mo_id": 42}
      ]'

Each entry results in one note on the inspection, e.g. **cpu**: Intel N100.
The response is a JSON list with ``status`` (``ok`` or ``error``, with a
``message``) per entry; add a ``uuid`` to an entry to identify it in the
response. All calls are logged in the input's actions.

Credits
=======

Authors
-------

* Nitrokey GmbH

Contributors
------------

* Nitrokey GmbH
