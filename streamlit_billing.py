from datetime import datetime, time, timedelta, date
import streamlit as st

def determine_billing_type(details):
    # Unpack details
    workcover_or_medicare = details['Workcover OR Medicare']
    monthly_fee = details['Monthly Fee'].strip('$ ')
    has_medicare_card = details['Has Medicare card']
    patient_age = details['Patient age']
    patient_has_concession_card = details['Patient has concenssion card']
    appointment_type = details['Appointment type']
    service_within_last_year = details['Has a non-telehalth service item been provided by a Doctor listed at this clinic within last 12 months']
    
    # Basic billing determination based on Medicare and monthly fee
    if has_medicare_card == 'Yes':
        if monthly_fee == '0':
            billing_type = 'Bulk Billed'
        else:
            billing_type = 'Private Billing (MBS Eligible)'
    else:
        billing_type = 'Private Billing (Not MBS Eligible)'

    # Adjust billing for telehealth conditions
    if appointment_type in ['Phone', 'Video'] and service_within_last_year == 'No':
        billing_type = 'Private Billing (Not MBS Eligible)'

    # Determine additional Bulk Billing Incentives
    bbi_items = []
    if billing_type == 'Bulk Billed':
        if patient_age < 16 or patient_has_concession_card == 'Yes':
            # Adding BBI depending on the condition
            bbi_items.append('10990')
            # For example, if you have specific conditions on when to use 75870, include it here
            # bbi_items.append('75870')

    return {
        'billing_type': billing_type,
        'bbi_items': bbi_items
    }
def get_non_urgent_in_person_service_item(appointment_details):

    # Extract necessary details from the appointment_details dictionary
    appointment_day = appointment_details['Day of appointment']
    appointment_time = appointment_details['Time of Appointment']
    appointment_length_str = appointment_details['Appointment Length']

    # Convert appointment time to a datetime object for easier comparison
    appointment_time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()

    # Extract the number of minutes from the string
    try:
        minutes = int(appointment_length_str.split(' ')[0])
    except ValueError:
        raise ValueError("Invalid format of appointment length. Please provide length as '<number> mins'.")

    # Define mappings based on appointment day and time
    service_map = {
        'weekday': {
            'before_8am': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')],
            'daytime': [(6, '3', '10990'), (20, '23', '75870'), (40, '36', '75870'), (60, '44', '75870'), (float('inf'), '123', '75870')],
            'after_8pm': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
        },
        'saturday': {
            'before_8am': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')],
            '8am_1pm': [(6, '3', '10990'), (20, '23', '75870'), (40, '36', '75870'), (60, '44', '75870'), (float('inf'), '123', '75870')],
            'after_1pm': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
        },
        'sunday_or_holiday': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
    }

    # Determine day and time category
    if appointment_day.lower() in ['saturday', 'sunday', 'public holiday']:
        day_key = 'saturday' if appointment_day.lower() == 'saturday' else 'sunday_or_holiday'
    else:
        day_key = 'weekday'
    
    # Select appropriate time category based on appointment time
    if appointment_time_obj < datetime.strptime("08:00", '%H:%M').time():
        time_category = service_map[day_key]['before_8am']
    elif day_key == 'saturday' and appointment_time_obj < datetime.strptime("13:00", '%H:%M').time():
        time_category = service_map[day_key]['8am_1pm']
    elif day_key == 'saturday' and appointment_time_obj >= datetime.strptime("13:00", '%H:%M').time():
        time_category = service_map[day_key]['after_1pm']
    elif day_key == 'weekday' and appointment_time_obj >= datetime.strptime("20:00", '%H:%M').time():
        time_category = service_map[day_key]['after_8pm']
    else:
        time_category = service_map[day_key]['daytime']

    # Find appropriate service item number based on appointment length
    for max_length, item_number, bbi_item in time_category:
        if minutes <= max_length:
            return {
                'Service Item Number': item_number,
                'Bulk Billing Incentive Item': bbi_item,
                'Reason': f"Non-urgent in-person appointment on a {appointment_day}, at {appointment_time}, for {minutes} minutes, assigned to service item {item_number}."
            }

    return {'Service Item Number': 'Unknown', 'Bulk Billing Incentive Item': None, 'Reason': "No valid service item found based on the provided details."}


def get_standard_time_based_service_item(appointment_details):
    # Time thresholds
    before_8am = time(8, 0)
    one_pm = time(13, 0)
    eight_pm = time(20, 0)
    
    # Extract necessary details from the appointment_details dictionary
    day_of_week = appointment_details['Day of appointment']
    appointment_time = appointment_details['Time of Appointment']
    appointment_length = appointment_details['Appointment Length']

    # Convert appointment time string to time object
    appointment_time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
    
    # Define mapping from (day part, length) to (service item, BBI)
    service_map = {
        'weekday': {
            'before_8am': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')],
            'daytime': [(6, '3', '10990'), (20, '23', '75870'), (40, '36', '75870'), (60, '44', '75870'), (float('inf'), '123', '75870')],
            'after_8pm': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
        },
        'saturday': {
            'before_8am': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')],
            '8am_1pm': [(6, '3', '10990'), (20, '23', '75870'), (40, '36', '75870'), (60, '44', '75870'), (float('inf'), '123', '75870')],
            'after_1pm': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
        },
        'sunday': [(6, '5000', '10990'), (20, '5020', '75870'), (40, '5040', '75870'), (60, '5060', '75870'), (float('inf'), '5071', '75870')]
    }
    
    # Determine day and time category
    if day_of_week.lower() in ['saturday', 'sunday']:
        day_key = 'saturday' if day_of_week.lower() == 'saturday' else 'sunday'
    else:
        day_key = 'weekday'
    
    # Select appropriate time category based on appointment time
    if day_key == 'sunday':
        time_category = service_map['sunday']
        category_reason = 'sunday'
    else:
        if appointment_time_obj < before_8am:
            time_category = service_map[day_key]['before_8am']
            category_reason = 'weekday before 8am'
        elif (day_key == 'saturday' and appointment_time_obj < one_pm) or (day_key == 'weekday' and appointment_time_obj < eight_pm):
            time_category = service_map[day_key]['8am_1pm'] if day_key == 'saturday' else service_map[day_key]['daytime']
            category_reason = 'saturday 8am-1pm' if day_key == 'saturday' else 'weekday 8am-8pm'
        else:
            time_category = service_map[day_key]['after_1pm'] if day_key == 'saturday' else service_map[day_key]['after_8pm']
            category_reason = 'saturday after 1pm' if day_key == 'saturday' else 'weekday after 8pm'
    
    # Find appropriate service item number based on appointment length
    appointment_length_minutes = int(appointment_length.split(' ')[0])
    for max_length, item_number, bbi_item in time_category:
        if appointment_length_minutes <= max_length:
            return {
                'Service Item Number': item_number,
                'Bulk Billing Incentive Item': bbi_item,
                'Reason': f"{day_of_week}, {category_reason}, in-person, appointment length {appointment_length_minutes} mins"
            }
    
    return {'Service Item Number': 'Unknown', 'Bulk Billing Incentive Item': None, 'Reason': 'No matching service item found'}
def get_urgent_in_person_service_item(appointment_details):
    # Extract necessary details from the appointment_details dictionary
    appointment_time = appointment_details['Time of Appointment']

    # Define time ranges for urgent appointments
    before_7am = ('00:00', '07:00')
    between_7am_and_11pm = ('07:00', '23:00')
    after_11pm = ('23:00', '23:59')
    
    # Convert appointment time to a datetime object for easier comparison
    appointment_time_obj = datetime.strptime(appointment_time, '%I:%M %p').time()
    
    # Mapping of time ranges to service item numbers for urgent appointments
    reason_detail = ""
    if appointment_time_obj < datetime.strptime(before_7am[1], '%H:%M').time():
        service_item_number = '599'
        reason_detail = "time before 7:00 AM"
    elif appointment_time_obj < datetime.strptime(after_11pm[0], '%H:%M').time():
        service_item_number = '597'
        reason_detail = "time between 7:00 AM and 11:00 PM"
    else:
        service_item_number = '599'
        reason_detail = "time after 11:00 PM"
    
    # Bulk Billing Incentive Item
    bbi_item = '10990'  # As specified, always 10990 for urgent in person appointments

    return {
        'Service Item Number': service_item_number,
        'Bulk Billing Incentive Item': bbi_item,
        'Reason': f"Urgent and in-person appointment, {reason_detail}"
    }
def get_non_urgent_telehealth_video_service_item(appointment_details):
    # Extract necessary details from the appointment_details dictionary
    appointment_length_str = appointment_details['Appointment Length']
    registered_for_mymedicare = appointment_details['Registered for My Medicare']

    # Extract the number of minutes from the string
    try:
        minutes = int(appointment_length_str.split(' ')[0])
    except ValueError:
        raise ValueError("Invalid format of appointment length. Please provide length as '<number> mins'.")

    # Determine the service item number and bulk billing incentive directly
    reason_detail = ""
    if minutes < 6:
        service_item_number = '91790'
        bbi_item = '10990'
        reason_detail = "less than 6 minutes"
    elif minutes <= 20:
        service_item_number = '91800'
        bbi_item = '75870'
        reason_detail = "6 to 20 minutes"
    elif minutes <= 40:
        service_item_number = '91801'
        bbi_item = '75880'
        reason_detail = "21 to 40 minutes"
    elif minutes <= 60:
        service_item_number = '91802'
        bbi_item = '75880'
        reason_detail = "41 to 60 minutes"
    else:
        service_item_number = '91920'
        bbi_item = '75880'
        reason_detail = "more than 60 minutes"

    return {
        'Service Item Number': service_item_number,
        'Bulk Billing Incentive Item': bbi_item,
        'Reason': f"Non-urgent and telehealth video appointment, duration: {reason_detail}, registered for MyMedicare: {'yes' if registered_for_mymedicare == 'Yes' else 'no'}"
    }
def get_urgent_telehealth_video_service_item():
    # For urgent telehealth video, the service item is fixed based on the rules provided:
    service_item_number = '92210'
    # The Bulk Billing Incentive Item for urgent telehealth video is also fixed:
    bbi_item = '10990'

    return {
        'Service Item Number': service_item_number,
        'Bulk Billing Incentive Item': bbi_item,
        'Reason': "Urgent telehealth video appointment, fixed service item and bulk billing incentive based on regulations"
    }
def get_non_urgent_telehealth_telephone_service_item(appointment_details):
    # Extract necessary details from the appointment_details dictionary
    appointment_length_str = appointment_details['Appointment Length']
    registered_for_mymedicare = appointment_details['Registered for My Medicare']

    # Extract the number of minutes from the string
    try:
        minutes = int(appointment_length_str.split(' ')[0])
    except ValueError:
        raise ValueError("Invalid format of appointment length. Please provide length as '<number> mins'.")

    # Define fallback service item number for non-registered MyMedicare
    fallback_service_item = '91891'  # Using an arbitrary item number as a generic example

    # Determine the service item number and bulk billing incentive directly
    reason_detail = ""
    if minutes < 6:
        service_item_number = '91890'
        bbi_item = '10990'
        reason_detail = "less than 6 minutes"
    elif minutes <= 20:
        service_item_number = '91891'
        bbi_item = '75870'
        reason_detail = "6 to 20 minutes"
    elif minutes <= 40:
        if registered_for_mymedicare:
            service_item_number = '91900'
            bbi_item = '75880'
            reason_detail = "21 to 40 minutes, registered for MyMedicare"
        else:
            service_item_number = fallback_service_item
            bbi_item = None
            reason_detail = "21 to 40 minutes, not registered for MyMedicare"
    else:
        if registered_for_mymedicare:
            service_item_number = '91910'
            bbi_item = '75880'
            reason_detail = "more than 40 minutes, registered for MyMedicare"
        else:
            service_item_number = fallback_service_item
            bbi_item = None
            reason_detail = "more than 40 minutes, not registered for MyMedicare"

    return {
        'Service Item Number': service_item_number,
        'Bulk Billing Incentive Item': bbi_item,
        'Reason': f"Non-urgent telehealth telephone appointment, {reason_detail}"
    }
def check_eligibility(last_service_date_str, months_limit):
    """
    Checks eligibility based on the last service date and a time limit in months.
    """
    if last_service_date_str.lower() == 'n/a':
        return True  # Always eligible if no previous service has been recorded.
    
    last_service_date = datetime.strptime(last_service_date_str, '%Y-%m-%d')
    eligibility_date = last_service_date + timedelta(days=months_limit * 30)  # Approximate month calculation.
    return datetime.now() >= eligibility_date

def get_gpmp_tca_service_item(appointment_details):
    """
    Determines the service item number, bulk billing incentive, and checks eligibility for GPMP and TCA services using a dictionary of appointment details.
    """
    service_type = appointment_details['Service Type']
    mode = appointment_details['Service Mode']
    last_service_date = appointment_details['Last Service Date']
    
    services = {
        'Preparation of GPMP': {
            'In person': '721',
            'Telehealth': '92024'
        },
        'Preparation of TCA': {
            'In person': '723',
            'Telehealth': '92025'
        },
        'Review of GPMP': {
            'In person': '732',
            'Telehealth': '92028'
        },
        'Review of TCA': {
            'In person': '732',
            'Telehealth': '92028'
        }
    }

    months_limit = 12 if 'Preparation' in service_type else 3  # 12 months for preparation, 3 months for reviews.
    
    item = services.get(service_type, {}).get(mode)
    if item:
        is_eligible = check_eligibility(last_service_date, months_limit)
        bbi_item = '10990'  # Assuming BBI is always applicable when bulk billed.

        reason = f"{service_type} ({'preparation' if 'Preparation' in service_type else 'review'}) for {'GPMP' if 'GPMP' in service_type else 'TCA'} in {mode.lower()} mode, eligibility checked based on last service date."
        return {
            'Service Item Number': item,
            'Bulk Billing Incentive Item': bbi_item,
            'Eligibility': is_eligible,
            'Reason': reason
        }
    else:
        return {
            'Error': 'Invalid service type or mode',
            'Reason': f"Attempted to retrieve service item for {service_type} in {mode}, which is not defined."
        }
def mhcp_billing_system(appointment_details):
    last_mhcp_date = appointment_details['Date of last MHCP']
    gp_has_training = appointment_details['GP has done specialised Mental Health Training'] == 'Yes'
    current_date = date.today()
    service_length = int(appointment_details['Appointment Length'].split()[0])
    appointment_type = appointment_details['Appointment type']
    is_review = appointment_details['MHCP Review performed during appointment?'] == 'Yes'
    
    # Convert string dates to datetime.date objects for comparison
    last_mhcp_datetime = datetime.strptime(last_mhcp_date, '%Y-%m-%d').date()
    days_since_last_mhcp = (current_date - last_mhcp_datetime).days

    # Determine service item number based on the appointment details and GP's training
    service_item_number = None
    training_info = "trained GP" if gp_has_training else "untrained GP"
    if appointment_type == 'In Person':
        if 20 <= service_length <= 40:
            service_item_number = '2715' if gp_has_training else '2700'
        elif service_length > 40:
            service_item_number = '2717' if gp_has_training else '2701'
    elif appointment_type in ['Voice', 'Video']:
        if 20 <= service_length <= 40:
            service_item_number = '92116' if gp_has_training else '92112'
        elif service_length > 40:
            service_item_number = '92117' if gp_has_training else '92113'

    reason_detail = f"{appointment_type}, {service_length} minutes, {training_info}, "

    # Check review conditions and adjust service item number if needed
    if is_review:
        if days_since_last_mhcp < 28:  # less than 4 weeks
            service_item_number = 'Too soon for review'
            reason_detail += "review too soon (<4 weeks since last MHCP)"
        elif days_since_last_mhcp < 90:  # less than 3 months but more than 4 weeks
            service_item_number = '2712'  # Assuming both trained and untrained GPs use the same item for the first review
            reason_detail += "review eligible (4 weeks to 3 months since last MHCP)"

    # Bulk Billing Incentive is standardized if patient is bulk billed
    bulk_billing_incentive_item = '10990' if appointment_details['Monthly Fee'] == '$0' else None

    # Check eligibility for claiming based on MHCP rules
    claiming_eligibility = days_since_last_mhcp >= 365  # Only one MHCP per year allowed
    if not claiming_eligibility:
        reason_detail += ", not eligible for claim (MHCP once per year)"

    # Output structured for MHCP specifics
    return {
        'Service Item Number': service_item_number,
        'Bulk Billing Incentive Item': bulk_billing_incentive_item,
        'Claiming Eligibility': claiming_eligibility,
        'Reason': f"MHCP during appointment, {reason_detail}"
    }
def parse_date(date_str):
    if date_str.lower() == 'n/a':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d')

def check_claim_eligibility(last_claim_date, frequency):
    if last_claim_date is None:
        return True  # Always eligible if no previous claim recorded
    today = datetime.now()
    if frequency == 'once':
        return False  # Only one claim allowed in the specified age range, and it's been claimed
    elif frequency == 'annually':
        return (today - last_claim_date).days >= 365
    elif frequency == 'every 3 years':
        return (today - last_claim_date).days >= 3 * 365
    return False
def determine_health_service(details):
    age = int(details['Patient age'])
    duration = details['Appointment Length']
    assessment_type = details['Appointment type']
    risk_factors = details.get('Risk factors', [])
    identifies_atsi = details.get('Identifies as ATSI', 'No') == 'Yes'

    # Initialize variables to avoid UnboundLocalError
    service_item = None
    bbi_item = None
    is_eligible = False
    reason = ""

    # Retrieve last claim dates from appointment details
    last_claim_dates = {
        '75 years and over health check': parse_date(details['Date of last 75yr+ health assessment']),
        '45 to 49 year health check': parse_date(details['Date of last 45yr to 49yr old health check']),
        '40 to 49 year diabetes check': parse_date(details['Date of last 40yr to 49yr old Diabetes check']),
        '30 years and over healthy heart check': parse_date(details['Date of last 30yr+ Healthy Heart check'])
    }

    # Service items mapping
    service_items = {
        # Detailed service items mapping as previously defined
    }

    if identifies_atsi:
        service_item = 715
        bbi_item = 10990
        is_eligible = True
        reason = "ATSI patient identified, automatically eligible regardless of other conditions."
        return {
            'Service Item Number': service_item,
            'Bulk Billing Incentive Item': bbi_item,
            'Eligibility': is_eligible,
            'Reason': reason
        }

    if assessment_type in service_items:
        service_info = service_items[assessment_type]
        last_claim_date = last_claim_dates.get(assessment_type, None)

        if duration in service_info['times']:
            duration_index = service_info['times'].index(duration)
            service_item = service_info['items'][duration_index]
            if age >= service_info['age_range'][0] and age <= service_info['age_range'][1]:
                if not service_info['risk_required'] or (service_info['risk_required'] and any(risk in risk_factors)):
                    if check_claim_eligibility(last_claim_date, service_info['claiming_frequency']):
                        bbi_item = 10990
                        is_eligible = True
                        reason = f"Eligible: Meets age, duration, and risk factor requirements for {assessment_type}."
                    else:
                        bbi_item = None
                        is_eligible = False
                        reason = f"Not eligible due to claiming frequency limitations for {assessment_type}."
                else:
                    bbi_item = None
                    is_eligible = False
                    reason = f"Not eligible due to missing required risk factors for {assessment_type}."
            else:
                bbi_item = None
                is_eligible = False
                reason = f"Not eligible due to age mismatch for {assessment_type}."
        else:
            bbi_item = None
            is_eligible = False
            reason = f"Invalid duration '{duration}' provided for {assessment_type}."
    else:
        reason = f"Invalid assessment type '{assessment_type}' provided."

    return {
        'Service Item Number': service_item if service_item else 'No valid service item',
        'Bulk Billing Incentive Item': bbi_item if bbi_item else 'No BBI applicable',
        'Eligibility': is_eligible,
        'Reason': reason
    }
def check_claim_frequency(last_claim_date_str, frequency):
    """
    Checks if the claim can be made again based on the last claim date and the specified frequency.
    """
    if last_claim_date_str.lower() == 'never':
        return True, "No previous claim recorded, always eligible."
    if frequency == 'No limit':
        return True, "No frequency limit, always eligible."

    last_claim_date = datetime.strptime(last_claim_date_str, '%Y-%m-%d')
    allowed_next_claim_date = last_claim_date
    if 'month' in frequency:
        month_count = int(frequency.split()[0])
        allowed_next_claim_date += timedelta(days=month_count * 30)  # Approximation for months
    is_eligible = datetime.now() >= allowed_next_claim_date
    reason = "Eligible to claim again" if is_eligible else f"Next eligible date is {allowed_next_claim_date}, currently not eligible."
    return is_eligible, reason

def get_specialized_medicare_service_item(appointment_details):
    """
    Determines the service item number for specialized Medicare services and checks if it's eligible to be claimed again.
    """
    service_description = appointment_details['Service Description']
    last_claim_date = appointment_details['Last Claim Date']
    number_of_claims_today = appointment_details.get('Number of Claims Today')

    services = {
        'Spirometry - 3 or more readings': {'item': '11505', 'frequency': '12 months'},
        'Spirometry - 1 or 2 readings': {'item': '11506', 'frequency': '12 months'},
        'ECG': {'item': '11707', 'frequency': 'No limit', 'daily_limit': 2},
        'Pregnancy Test': {'item': '73806', 'frequency': 'No limit'}
    }

    service = services.get(service_description)
    if service:
        service_item_choice_reason = f"Service item {service['item']} chosen based on the provided service description '{service_description}'."
        if 'daily_limit' in service and number_of_claims_today is not None:
            if number_of_claims_today >= service['daily_limit']:
                return {
                    'Service Item Number': service['item'],
                    'Bulk Billing Incentive Item': '10990',
                    'Eligibility': False,
                    'Reason': f"Daily limit of {service['daily_limit']} claims reached for {service_description}. " + service_item_choice_reason
                }

        is_eligible, eligibility_reason = check_claim_frequency(last_claim_date, service['frequency'])
        return {
            'Service Item Number': service['item'],
            'Bulk Billing Incentive Item': '10990',
            'Eligibility': is_eligible,
            'Reason': eligibility_reason + " " + service_item_choice_reason
        }
    else:
        return {
            'Error': 'Invalid service description',
            'Reason': f"No service found matching the description '{service_description}'. Unable to determine a service item."
        }
def infer_service_type(performed, reviewed):
    if performed == 'Yes' and reviewed == 'No':
        return 'Preparation'
    elif reviewed == 'Yes':
        return 'Review'
    return None

def check_eligibility_for_service(last_service_date, service, service_type):
    if last_service_date.lower() == 'n/a':
        return True  # Always eligible if no previous service has been recorded.
    last_service_date = datetime.strptime(last_service_date, '%Y-%m-%d')
    time_since_last = (datetime.now() - last_service_date).days
    if service_type == 'Preparation':
        return time_since_last > 365  # More than a year ago
    elif service_type == 'Review':
        return time_since_last > 90  # More than three months ago
    return False

def get_service_item(appointment_details):
    service_mapping = {
        'GPMP': {
            'Preparation': '721',
            'Review': '732'
        },
        'TCA': {
            'Preparation': '723',
            'Review': '732'
        },
        'MHCP': {
            'Preparation': '92024',
            'Review': '92028'
        }
    }
    
    selected_service = None
    for service in ['GPMP', 'TCA', 'MHCP']:
        last_service_date = appointment_details.get(f'Date of last {service}', 'n/a')
        if last_service_date != 'n/a':
            selected_service = service
            break

    if not selected_service:
        return {'Service Item Number': 'None', 'Bulk Billing Incentive Item': 'None', 'Eligibility': False, 'Reason': 'No valid service data found or all services are without dates'}

    service_type = infer_service_type(appointment_details.get(f'{selected_service} performed during appointment?', 'No'),
                                      appointment_details.get(f'{selected_service} Review performed during appointment?', 'No'))

    if service_type:
        item_number = service_mapping[selected_service][service_type]
        last_service_date = appointment_details.get(f'Date of last {selected_service}', 'n/a')
        is_eligible = check_eligibility_for_service(last_service_date, selected_service, service_type)
        reason = f"Service type '{service_type}' for '{selected_service}' selected. Item number '{item_number}' is chosen based on the service type."
        return {
            'Service Item Number': item_number,
            'Bulk Billing Incentive Item': '10990',
            'Eligibility': is_eligible,
            'Reason': reason
        }
    else:
        return {
            'Service Item Number': 'None', 
            'Bulk Billing Incentive Item': 'None', 
            'Eligibility': False, 
            'Reason': 'Invalid or missing data for determining service type.'
        }
def determine_billing_type(details):
    # Safely get details with default values if keys are missing
    workcover_or_medicare = details.get('Workcover OR Medicare', 'Medicare')  # Default to 'Medicare' if not specified
    monthly_fee = details.get('Monthly Fee', '$0').strip('$ ')
    has_medicare_card = details.get('Has Medicare card', 'No')
    patient_age = details.get('Patient age', 0)  # Default to 0 if not specified
    patient_has_concession_card = details.get('Patient has concenssion card', 'No')
    appointment_type = details.get('Appointment type', 'In Person')
    service_within_last_year = details.get('Has a non-telehealth service item been provided by a Doctor listed at this clinic within last 12 months', 'No')
    
    billing_reason = ""
    # Basic billing determination based on Medicare and monthly fee
    if has_medicare_card == 'Yes' and monthly_fee == '0':
        billing_type = 'Bulk Billed'
        billing_reason = "Eligible for bulk billing as patient has a Medicare card and no monthly fee is charged."
    elif has_medicare_card == 'Yes':
        billing_type = 'Private Billing (MBS Eligible)'
        billing_reason = "Eligible for private billing under Medicare benefits as patient has a Medicare card."
    else:
        billing_type = 'Private Billing (Not MBS Eligible)'
        billing_reason = "Not eligible for Medicare benefits; private billing applies."

    # Adjust billing for telehealth conditions
    if appointment_type in ['Phone', 'Video'] and service_within_last_year == 'No':
        billing_type = 'Private Billing (Not MBS Eligible)'
        billing_reason += " Adjusted to private billing as the appointment is via telehealth and no in-person service was provided in the last year."

    # Determine additional Bulk Billing Incentives
    bbi_items = []
    if billing_type == 'Bulk Billed':
        if int(patient_age) < 16 or patient_has_concession_card == 'Yes':
            bbi_items.append('10990')  # Example BBI item number
            billing_reason += " Additional bulk billing incentive applied due to age under 16 or possession of a concession card."

    return {
        'billing_type': billing_type,
        'bbi_items': bbi_items,
        'billing_reason': billing_reason
    }
def comprehensive_billing_and_service_system(appointment_details):
    # Determine basic billing type
    billing_info = determine_billing_type(appointment_details)
    
    # Initialize the response for service items
    service_item_details = {
        'Service Item Number': 'Unknown',
        'Bulk Billing Incentive Item': None,
        'Claiming Eligibility': True,
        'Reason': 'No specialized service matched; default to generic assessment.'
    }
    
    # Check specialized service provisions based on the appointment details
    specialized_handled = False
    if appointment_details.get('MHCP performed during appointment?', 'No') == 'Yes' or appointment_details.get('MHCP Review performed during appointment?', 'No') == 'Yes':
        service_item_details = mhcp_billing_system(appointment_details)
        specialized_handled = True
    elif appointment_details.get('GPMP performed during appointment?', 'No') == 'Yes' or appointment_details.get('GPMP Review performed during appointment?', 'No') == 'Yes':
        service_item_details = get_gpmp_tca_service_item({
            'Service Type': 'Preparation of GPMP' if appointment_details['GPMP performed during appointment?'] == 'Yes' else 'Review of GPMP',
            'Service Mode': 'In person',  # or 'Telehealth' depending on context
            'Last Service Date': appointment_details['Date of last GPMP']
        })
        specialized_handled = True
    elif appointment_details.get('TCA performed during appointment?', 'No') == 'Yes' or appointment_details.get('TCA Review performed during appointment?', 'No') == 'Yes':
        service_item_details = get_gpmp_tca_service_item({
            'Service Type': 'Preparation of TCA' if appointment_details['TCA performed during appointment?'] == 'Yes' else 'Review of TCA',
            'Service Mode': 'In person',  # or 'Telehealth' depending on context
            'Last Service Date': appointment_details['Date of last TCA']
        })
        specialized_handled = True

    # Handle non-specialized services if no specialized service was detected
    if not specialized_handled:
        if appointment_details.get('Spirometry performed during appointment', 'No') == 'Yes':
            service_item_details['Service Item Number'] = '11505' if int(appointment_details.get('Spirometry readings count', 0)) >= 3 else '11506'
            service_item_details['Bulk Billing Incentive Item'] = '10990'
            service_item_details['Claiming Eligibility'] = True
            service_item_details['Reason'] = 'Spirometry performed, service item based on number of readings.'
            specialized_handled = True

        if appointment_details.get('ECG Performed during appointment', 'No') == 'Yes' and not specialized_handled:
            service_item_details['Service Item Number'] = '11707'
            service_item_details['Bulk Billing Incentive Item'] = '10990'
            service_item_details['Claiming Eligibility'] = True
            service_item_details['Reason'] = 'ECG performed, eligible for service item 11707.'
            specialized_handled = True

        if appointment_details.get('Pregnancy Test Performed during appointment', 'No') == 'Yes' and not specialized_handled:
            service_item_details['Service Item Number'] = '73806'
            service_item_details['Bulk Billing Incentive Item'] = '10990'
            service_item_details['Claiming Eligibility'] = True
            service_item_details['Reason'] = 'Pregnancy test performed, eligible for service item 73806.'
            specialized_handled = True 
    if specialized_handled and not service_item_details.get('Claiming Eligibility', True):
        service_item_details = get_standard_time_based_service_item(appointment_details)

    # Handle non-specialized services if no specialized service was detected
    if service_item_details['Service Item Number'] == 'Unknown':
        if appointment_details['Appointment urgency'] == 'Yes':
            service_item_details = get_urgent_in_person_service_item(appointment_details) if appointment_details['Appointment type'] == 'In Person' else get_urgent_telehealth_video_service_item()
        else:
            if 'Video' in appointment_details['Appointment type']:
                service_item_details = get_non_urgent_telehealth_video_service_item(appointment_details)
            elif 'In Person' == appointment_details['Appointment type']:
                service_item_details = get_non_urgent_in_person_service_item(appointment_details)
            else:
                service_item_details = get_non_urgent_telehealth_telephone_service_item(appointment_details)

    # Aggregate all information
    result = {
        'Billing Type': billing_info['billing_type'],
        'Billing Reason': billing_info.get('billing_reason', 'Billing details not provided.'),
        'Service Item Number': service_item_details.get('Service Item Number'),
        'Bulk Billing Incentive Item': service_item_details.get('Bulk Billing Incentive Item'),
        'Claiming Eligibility': service_item_details.get('Claiming Eligibility', True),
        'Service Reason': service_item_details.get('Reason', 'No specific service reason provided.')
    }

    return result

def main():
    st.title("Medical Billing System")

    with st.form("appointment_form"):
        # Patient Details
        st.subheader("Patient Details")
        workcover_or_medicare = st.selectbox('Workcover or Medicare', ['Medicare', 'Workcover'], index=0)
        patient_age = st.number_input('Patient Age', min_value=0, max_value=120, value=45)
        active_member = st.selectbox('Active Member', ['Yes', 'No'], index=0)
        monthly_fee = st.text_input('Monthly Fee', value='$0')
        has_medicare_card = st.selectbox('Has Medicare Card', ['Yes', 'No'], index=0)
        registered_for_my_medicare = st.selectbox('Registered for My Medicare', ['Yes', 'No'], index=0)
        patient_has_concession_card = st.selectbox('Patient has Concession Card', ['Yes', 'No'], index=1)
        identifies_as_atsi = st.selectbox('Identifies as ATSI', ['Yes', 'No'], index=1)

        # Appointment Time
        st.subheader("Appointment Time")
        appointment_urgency = st.selectbox('Appointment Urgency', ['Yes', 'No'], index=1)
        appointment_type = st.selectbox('Appointment Type', ['In Person', 'Phone', 'Video'], index=0)
        day_of_appointment = st.selectbox('Day of Appointment', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], index=0)
        time_of_appointment = st.time_input('Time of Appointment', datetime.strptime('3:00 PM', '%I:%M %p'))
        appointment_length = st.text_input('Appointment Length', value='45 mins')
        public_holiday = st.selectbox('Public Holiday', ['Yes', 'No'], index=1)

        # Additional Details
        st.subheader("Additional Details")
        non_telehealth_item_provided = st.selectbox('Non-telehealth Service Item Provided', ['Yes', 'No'], index=1)
        gp_has_mental_health_training = st.selectbox("Has the GP completed specialized mental health training?", ["Yes", "No"], index=0)
        # Eligibility checkboxes or select boxes depending on the application requirements
        patient_meets_requirements_75yr = st.selectbox("Does the patient meet the requirements for a 75+ year health assessment?", ["Yes", "No"], index=1)
        patient_meets_requirements_45_to_49yr = st.selectbox("Does the patient meet the requirements for a 45 to 49 year health check?", ["Yes", "No"], index=0)
        patient_meets_requirements_40_to_49yr = st.selectbox("Does the patient meet the requirements for a 40 to 49 year diabetes check?", ["Yes", "No"], index=1)
        patient_meets_requirements_30yr_plus = st.selectbox("Does the patient meet the requirements for a 30+ year healthy heart check?", ["Yes", "No"], index=0)
        
        # Clinical and Health Assessments
        st.subheader("Clinical and Health Assessments")
        gpmp_performed = st.selectbox('GPMP Performed During Appointment?', ['Yes', 'No'], index=1)
        gpmp_review_performed = st.selectbox('GPMP Review Performed During Appointment?', ['Yes', 'No'], index=1)
        tca_performed = st.selectbox('TCA Performed During Appointment?', ['Yes', 'No'], index=1)
        tca_review_performed = st.selectbox('TCA Review Performed During Appointment?', ['Yes', 'No'], index=1)
        mhcp_performed = st.selectbox('MHCP Performed During Appointment?', ['Yes', 'No'], index=1)
        mhcp_review_performed = st.selectbox('MHCP Review Performed During Appointment?', ['Yes', 'No'], index=0)
        health_assessment_75yr = st.selectbox('75yr+ Health Assessment Performed During Appointment?', ['Yes', 'No'], index=1)
        health_check_45_to_49yr = st.selectbox('45yr to 49yr Old Health Check Performed During Appointment?', ['Yes', 'No'], index=1)
        diabetes_check_40_to_49yr = st.selectbox('40yr to 49yr Old Diabetes Check Performed During Appointment?', ['Yes', 'No'], index=1)
        healthy_heart_check_30yr = st.selectbox('30yr+ Healthy Heart Check Performed During Appointment?', ['Yes', 'No'], index=1)
        spirometry_performed = st.selectbox('Spirometry Performed During Appointment?', ['Yes', 'No'], index=1)
        ecg_performed = st.selectbox('ECG Performed During Appointment?', ['Yes', 'No'], index=1)
        pregnancy_test_performed = st.selectbox('Pregnancy Test Performed During Appointment?', ['Yes', 'No'], index=1)

        # Dates of Last Assessments and Checks
        st.subheader("Dates of Last Assessments and Checks")
        date_of_last_mhcp = st.text_input('Date of Last MHCP', value='2023-01-15')
        date_of_last_mhcp_review = st.text_input('Date of Last MHCP Review', value='2024-03-15')
        date_of_last_gpmp = st.text_input('Date of Last GPMP', value='2022-10-01')
        date_of_last_gpmp_review = st.text_input('Date of Last GPMP Review', value='2022-11-01')
        date_of_last_tca = st.text_input('Date of Last TCA', value='2022-09-01')
        date_of_last_tca_review = st.text_input('Date of Last TCA Review', value='2024-10-01')
        date_of_last_75yr_health_assessment = st.text_input("Date of last 75+ year health assessment (YYYY-MM-DD)", 'N/A')
        date_of_last_45_to_49yr_health_check = st.text_input("Date of last 45 to 49 year health check (YYYY-MM-DD)", 'N/A')
        date_of_last_40_to_49yr_diabetes_check = st.text_input("Date of last 40 to 49 year diabetes check (YYYY-MM-DD)", 'N/A')
        date_of_last_30yr_plus_healthy_heart_check = st.text_input("Date of last 30+ year healthy heart check (YYYY-MM-DD)", 'N/A')
        date_of_last_spirometry = st.text_input('Date of Last Spirometry', value='2023-08-20')

        submitted = st.form_submit_button("Submit")
        if submitted:
            appointment_details = {
                'Workcover OR Medicare': workcover_or_medicare,
                'GP has done specialised Mental Health Training': gp_has_mental_health_training,
                'Appointment urgency': appointment_urgency,
                'Patient age': patient_age,
                'Active Member': active_member,
                'Monthly Fee': monthly_fee,
                'Has Medicare card': has_medicare_card,
                'Registered for My Medicare': registered_for_my_medicare,
                'Patient has concession card': patient_has_concession_card,
                'Has a non-telehealth service item been provided by a Doctor listed at this clinic within last 12 months': non_telehealth_item_provided,
                'Appointment type': appointment_type,
                'Day of appointment': day_of_appointment,
                'Time of Appointment': time_of_appointment.strftime('%I:%M %p'),  # Format time as needed
                'Appointment Length': appointment_length,
                'Public Holiday': public_holiday,
                'GPMP performed during appointment?': gpmp_performed,
                'GPMP Review performed during appointment?': gpmp_review_performed,
                'TCA performed during appointment?': tca_performed,
                'TCA Review performed during appointment?': tca_review_performed,
                'MHCP performed during appointment?': mhcp_performed,
                'MHCP Review performed during appointment?': mhcp_review_performed,
                '75yr+ health assessment performed during appointment?': health_assessment_75yr,
                '45yr to 49yr old health check performed during appointment?': health_check_45_to_49yr,
                '40yr to 49yr old Diabetes check performed during appointment?': diabetes_check_40_to_49yr,
                '30yr+ Healthy Heart check performed during appointment?': healthy_heart_check_30yr,
                'Date of last MHCP': date_of_last_mhcp,
                'Date of last MHCP Review': date_of_last_mhcp_review,
                'Date of last GPMP': date_of_last_gpmp,
                'Date of last GPMP review': date_of_last_gpmp_review,
                'Date of last TCA': date_of_last_tca,
                'Date of last TCA Review': date_of_last_tca_review,
                'Date of last 75yr+ health assessment': date_of_last_75yr_health_assessment,
                'Date of last 45yr to 49yr old health check': date_of_last_45_to_49yr_health_check,
                'Date of last 40yr to 49yr old Diabetes check': date_of_last_40_to_49yr_diabetes_check,
                'Date of last 30yr+ Healthy Heart check': date_of_last_30yr_plus_healthy_heart_check,
                'Patient meets requirements for 75yr+ health assessment': patient_meets_requirements_75yr,
                'Patient meets requirements for 45yr to 49yr health check': patient_meets_requirements_45_to_49yr,
                'Patient meets requirements for 40yr to 49yr health check': patient_meets_requirements_40_to_49yr,
                'Patient meets requirements for 30yr+ healthy heart check': patient_meets_requirements_30yr_plus,
                'Date of last spirometry': date_of_last_spirometry,
                'Spirometry performed during appointment': spirometry_performed,
                'ECG Performed during appointment': ecg_performed,
                'Pregnancy Test Performed during appointment': pregnancy_test_performed,
                'Identifies as ATSI': identifies_as_atsi
            }
            # Call a function to process these details
            result = comprehensive_billing_and_service_system(appointment_details)
            st.write(result)

if __name__ == "__main__":
    main()
