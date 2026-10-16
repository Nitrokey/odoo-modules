This addon lets an IoT device send measurement values (e.g. CPU, RAM,
storage) to Odoo and attaches them to the quality control (`qc.inspection`)
of a Manufacturing Order.

Each key/value pair is posted as a separate note in the chatter of the
inspection of the given Manufacturing Order. It builds on `iot_input_oca`
(device authentication, per-key inputs, call logging) and
`quality_control_mrp_oca`.
