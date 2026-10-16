The Manufacturing Order must already have a quality inspection. The device
sends all values in one request to `/iot/<serial>/multi_input` (the serial
and passphrase of the *Multi input* input). The ID of the Manufacturing
Order (`mo_id`) must be part of every entry:

    curl -X POST https://odoo.example.com/iot/<serial>/multi_input \
      --data-urlencode 'passphrase=<passphrase>' \
      --data-urlencode 'values=[
        {"address": "cpu", "value": "Intel N100", "mo_id": 42},
        {"address": "ram", "value": "16 GB", "mo_id": 42},
        {"address": "storage", "value": "512 GB", "mo_id": 42}
      ]'

Each entry results in one note on the inspection, e.g. **cpu**: Intel N100.
The response is a JSON list with `status` (`ok` or `error`, with a
`message`) per entry; add a `uuid` to an entry to identify it in the
response. All calls are logged in the input's actions.
