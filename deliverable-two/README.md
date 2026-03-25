# Deliverable Two

Step 2 evaluates how orthopedic practices handle inbound scheduling calls. The work product lives in [`outputs/orthopedic_practices_with_scheduling_information.csv`](/D:/kyron-applied-software/deliverable-two/outputs/orthopedic_practices_with_scheduling_information.csv).

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
- `A_followup_working_hours`
- `B_new_working_hours`
- `C_followup_after_hours`
- `D_new_after_hours`
- `working_hours_call_completed`
- `after_hours_call_completed`
- `working_hours_call_datetime`
- `after_hours_call_datetime`
- `working_hours_entrypoint`
- `after_hours_entrypoint`
- `working_hours_scheduler_endpoint`
- `after_hours_scheduler_endpoint`
- `working_hours_confidence`
- `after_hours_confidence`
- `call_attempts_total`
- `last_call_outcome`
- `notes`

Recommended values for the A/B/C/D classification columns:
- `human`
- `automated`
- `voicemail`
- `mixed`
- `unknown`
- `not_tested`

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
- `high`
- `medium`
- `low`

## Population Rules

- A single working-hours call may populate both `A_followup_working_hours` and `B_new_working_hours` if the menu or staff answer distinguishes them clearly.
- A single after-hours call may populate both `C_followup_after_hours` and `D_new_after_hours` if the after-hours behavior is clear.
- If the system does not distinguish between new and follow-up patients, populate both relevant categories with the same value and explain that in `notes`.
- Use `voicemail` only when the caller is clearly asked to leave a message.
- Use `unknown` when the behavior is inconclusive.

Recommended note style:
- `WH: IVR -> appointments -> live scheduler`
- `WH: receptionist said new and follow-up both handled by staff`
- `AH: closed message, no scheduling option`
- `AH: automated callback request for new patients`
