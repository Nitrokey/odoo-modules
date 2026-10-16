1.  Go to IoT \> Config \> Add a new Device. It shows a configuration URL.
2.  Send a POST request with the parameter `template=Quality Control
    measurements` to that URL (once; the URL is valid for a single use):

        curl -X POST -d 'template=Quality Control measurements' <configuration URL>

    This creates the device with these inputs and returns their serials
    and passphrases as JSON:

    - *Multi input* (function `parse_multi_input`), the entry point of the
      device. Its **serial** and **passphrase** are used for the requests
      described in Usage.
    - one input per measurement key (`cpu`, `ram`, `storage`), using the
      function `post_measurement` of the model *iot.quality.control*. The
      **address** of the input is the key name sent by the device.
3.  To accept more keys, add inputs to the template (IoT \> Config \>
    Templates) before step 2, or directly to the device afterwards,
    copying an existing one: model `iot.quality.control`, function
    `post_measurement`, params `{"address": "<key>"}`. Keys that are not
    configured as active inputs are rejected.
4.  Optional: restrict the notes to the inspection of one QC test by
    creating the system parameter `iot_quality_control.qc_test_id`
    (Settings \> Technical \> System Parameters) with the database ID of
    the *qc.test*. Without it, the open inspection of the Manufacturing
    Order is used (the most recent one if there are several).
