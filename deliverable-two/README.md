# Deliverable Two

Step 2 evaluates how orthopedic practices handle inbound scheduling calls. The work product lives in [`outputs/orthopedic_practices_with_scheduling_information.csv`](/D:/kyron-applied-software/deliverable-two/outputs/orthopedic_practices_with_scheduling_information.csv).

This deliverable is structured around a one-call-per-practice default. Not every practice will be reached, and not every call will be accepted or produce a complete classification.

## Call Script

Use the shortest truthful human script possible.

Opening:
- `Hi, I'm calling to understand how appointment scheduling works.`

If classifying new-patient scheduling:
- `If I were a new patient and wanted to schedule, would that go to a person or an automated system?`

If classifying follow-up scheduling:
- `If I were an existing patient trying to schedule a follow-up, would that go to a person or an automated system?`

If asked to continue further:
- `That answers my question, thank you. I need to go.`

If asked who is calling or why:
- `I'm an individual doing a research exercise about appointment scheduling workflows.`

Constraints:
- Do not use autodialers, prerecorded audio, or AI calling agents.
- Do not book an appointment.
- Do not claim affiliation with Kyron Medical or any company.
- Hang up once behavior is clear, ideally within about one minute.

## IVR / AI Flow

For automated systems, classify the scheduling path rather than trying to complete it.

1. Call the main line.
2. Record the entrypoint:
   - `human`
   - `ivr`
   - `voicemail`
   - `after_hours_message`
   - `busy`
   - `no_answer`
3. If an IVR answers, follow the shortest path toward:
   - `appointments`
   - `scheduling`
   - `new patients`
   - `existing patients`
4. Stop once the endpoint is clear:
   - `human`
   - `automated`
   - `voicemail`
   - `callback_request`
   - `unknown`
5. Hang up after the classification is clear.

## Output CSV

Primary output:
- [`outputs/orthopedic_practices_with_scheduling_information.csv`](/D:/kyron-applied-software/deliverable-two/outputs/orthopedic_practices_with_scheduling_information.csv)

Current base columns already present:
- `practice_id`
- `practice_name`
- `phone`
- `street`
- `city`
- `state`
- `zip_code`
- `website`
- `location_count`
- `source`
- `source_url`

Step 2 columns to add/populate:
- `call_attempted`
- `call_scenario`
- `call_completed`
- `call_datetime`
- `working_hours_entrypoint`
- `after_hours_entrypoint`
- `working_hours_scheduler_endpoint`
- `after_hours_scheduler_endpoint`
- `confidence`
- `confidence`
- `notes`

Recommended values for `call_attempted`:
- `yes`
- `no`

Recommended values for `call_scenario`:
- `A`
- `B`
- `C`
- `D`

Recommended values for `call_completed`:
- `yes`
- `no`

Recommended values for `working_hours_entrypoint` and `after_hours_entrypoint`:
- `human`
- `ivr`
- `voicemail`
- `after_hours_message`
- `busy`
- `no_answer`

Recommended values for `working_hours_scheduler_endpoint` and `after_hours_scheduler_endpoint`:
- `human`
- `automated`
- `voicemail`
- `callback_request`
- `unknown`

Recommended values for confidence:
- `high`: High chance of successful scheduling / follow-up.
- `medium`: Medium chance of successful scheduling / follow-up.
- `low`: Low chance of successful scheduling / follow-up.

## Population Rules

- `call_scenario` should record which scenario the single observed call represents:
  - `A` = follow-up patient during working hours
  - `B` = new patient during working hours
  - `C` = follow-up patient outside working hours
  - `D` = new patient outside working hours
- `call_attempted` should be `yes` when a call was placed and `no` otherwise.
- `call_completed` should be `yes` when you were able to classify the scheduling behavior from that call and `no` when the call did not yield a usable result.
- `call_datetime` should store the time of the actual observed call.
