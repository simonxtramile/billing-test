import streamlit as st
from datetime import datetime
def get_standard_service_item(start_time, length, day_of_week, urgent=False):
    """
    Determines the correct standard service item number based on the appointment's start time,
    length, and day of the week.
    """
    # Convert start time to a comparable format
    start_hour = int(start_time.split(':')[0])
    start_minute = int(start_time.split(':')[1])
    service_item = None
    
    if urgent:
        if day_of_week in ['Saturday', 'Sunday', 'Public Holiday']:
            return 599, 10990  # Assuming all urgent appointments on weekends and public holidays use this item
        elif start_time < '07:00':
            return 599, 10990
        elif '07:00' <= start_time <= '23:00':
            return 597, 10990
        else:  # After 23:00
            return 599, 10990

    # Determine if the appointment is during a weekday, Saturday, or Sunday/Public Holiday
    if day_of_week in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if start_hour < 8:
            time_frame = 'before_8am'
        elif 8 <= start_hour < 20 or (start_hour == 20 and start_minute == 0):
            time_frame = '8am_8pm'
        else:
            time_frame = 'after_8pm'
    elif day_of_week == 'Saturday':
        if start_hour < 8:
            time_frame = 'before_8am'
        elif 8 <= start_hour < 13 or (start_hour == 13 and start_minute == 0):
            time_frame = '8am_1pm'
        else:
            time_frame = 'after_1pm'
    else:  # Sunday or Public Holiday
        time_frame = 'all_day'

    # Map the appointment length to the service item number
    if length < 6:
        service_item = 5000
    elif 6 <= length <= 20:
        service_item = {'before_8am': 5020, '8am_8pm': 23, 'after_8pm': 5020, '8am_1pm': 23, 'after_1pm': 5020, 'all_day': 5020}[time_frame]
    elif 20 < length <= 40:
        service_item = {'before_8am': 5040, '8am_8pm': 36, 'after_8pm': 5040, '8am_1pm': 36, 'after_1pm': 5040, 'all_day': 5040}[time_frame]
    elif 40 < length <= 60:
        service_item = {'before_8am': 5060, '8am_8pm': 44, 'after_8pm': 5060, '8am_1pm': 44, 'after_1pm': 5060, 'all_day': 5060}[time_frame]
    else:  # length > 60
        service_item = 5071  # This item number is consistent across all provided rules for appointments over 60 minutes

    # Add Bulk Billing Incentive Item if applicable based on the time frame
    if time_frame in ['before_8am', 'after_8pm', 'all_day'] and service_item != 5000:
        # This condition is simplified; actual logic might differ based on more specific rules
        bbi_item = 10990
    elif service_item != 5000:
        bbi_item = 75870
    else:
        bbi_item = None

    return service_item, bbi_item

def get_specialized_service_item(appointment_type, telehealth):
    # Mapping specialized services to their item numbers
    service_items = {
        'GPMP': 721 if not telehealth else 92024,
        'TCA': 723 if not telehealth else 92025,
        'MHCP': 2715,  # Example, actual item depends on more conditions
        'Health Assessment': 701,  # Example, actual item depends on age, etc.
    }
    return service_items.get(appointment_type, None)

def determine_billing(medicare_card, evercare_paid, age, has_pension_card, work_capacity_certificate, appointment_type, telehealth, seen_doctor_in_person_last_12_months, registered_with_mymedicare):
    billing_label = "Private Billing"
    service_items = []

    # Handling Telehealth appointments with specific conditions
    if telehealth:
        if not seen_doctor_in_person_last_12_months:
            return "Private Billing (Not MBS Eligible)", service_items
        elif not medicare_card:
            return "Private Billing (Not MBS Eligible)", service_items
        else:
            # For patients with Medicare cards and who have seen a doctor in-person within the last 12 months
            if evercare_paid == 0:
                billing_label = "Bulk Billed"
                if age < 16 or has_pension_card:
                    service_items.append(10990)  # Adding Bulk Billing Incentive (BBI)
            else:
                billing_label = "Private Billing (MBS Eligible)"
    else:
        # Non-telehealth appointments follow existing logic
        if not medicare_card:
            return "Private Billing (Not MBS Eligible)", service_items
        if work_capacity_certificate:
            # Assuming logic to prompt the doctor for Workcover or Medicare choice is handled externally
            # Placeholder for prompt result: 'Medicare'
            if medicare_card:
                billing_label = "Bulk Billed" if evercare_paid == 0 else "Private Billing (MBS Eligible)"
        else:
            if medicare_card:
                if evercare_paid == 0:
                    billing_label = "Bulk Billed"
                    if age < 16 or has_pension_card:
                        service_items.append(10990)  # Adding BBI
                else:
                    billing_label = "Private Billing (MBS Eligible)"
    
    # Adjust service item based on specialized services
    specialized_item = get_specialized_service_item(appointment_type, telehealth)
    if specialized_item:
        service_items.append(specialized_item)
    
    return billing_label, service_items


def get_billing_info(appointment_details):
    start_time = appointment_details['start_time']
    length = appointment_details['length']
    day_of_week = appointment_details['day_of_week']
    medicare_card = appointment_details['medicare_card']
    evercare_paid = appointment_details['evercare_paid']
    age = appointment_details['age']
    work_capacity_certificate = appointment_details['work_capacity_certificate']
    has_pension_card = appointment_details['has_pension_card']
    appointment_type = appointment_details.get('appointment_type', 'Standard')
    telehealth = appointment_details['telehealth']
    seen_doctor_in_person_last_12_months = appointment_details['seen_doctor_in_person_last_12_months']
    registered_with_mymedicare = appointment_details['registered_with_mymedicare']
    

    # Determine the billing label and additional service items
    billing_label, additional_items = determine_billing(
        medicare_card, evercare_paid, age, has_pension_card, work_capacity_certificate, appointment_type, telehealth, seen_doctor_in_person_last_12_months, registered_with_mymedicare
    )

    # For standard appointments, dynamically choose the service item
    if appointment_type == 'Standard':
        standard_item = get_standard_service_item(start_time, length, day_of_week)
        additional_items.append(standard_item)

    return {
        "billing_label": billing_label,
        "service_items": additional_items
    }
#billing_info = get_billing_info(appointment_details)
#print(billing_info)

def app():
    st.title('Appointment Billing Calculator')

    # User inputs for appointment details
    start_time = st.time_input('Appointment Start Time', datetime.now()).strftime('%H:%M')
    length = st.number_input('Appointment Length (in minutes)', min_value=1, value=20)
    day_of_week = st.selectbox('Day of the Week', ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    medicare_card = st.checkbox('Has Medicare Card', value=True)
    evercare_paid = st.number_input('Evercare Monthly Fee', min_value=0, value=0, format='%d')
    age = st.number_input('Age', min_value=0, value=30, format='%d')
    work_capacity_certificate = st.checkbox('Work Capacity Certificate')
    has_pension_card = st.checkbox('Has Pension Card')
    appointment_type = st.selectbox('Appointment Type', ['Standard', 'GPMP', 'TCA', 'MHCP', 'Health Assessment'])
    telehealth = st.checkbox('Telehealth Appointment')
    seen_doctor_in_person_last_12_months = st.checkbox('Seen Doctor in Person Last 12 Months', value=True)
    registered_with_mymedicare = st.checkbox('Registered with MyMedicare', value=True)

    appointment_details = {
        'start_time': start_time,
        'length': length,
        'day_of_week': day_of_week,
        'medicare_card': medicare_card,
        'evercare_paid': evercare_paid,
        'age': age,
        'work_capacity_certificate': work_capacity_certificate,
        'has_pension_card': has_pension_card,
        'appointment_type': appointment_type,
        'telehealth': telehealth,
        'seen_doctor_in_person_last_12_months': seen_doctor_in_person_last_12_months,
        'registered_with_mymedicare': registered_with_mymedicare,
    }

    if st.button('Calculate Billing'):
        billing_info = get_billing_info(appointment_details)
        st.write(billing_info)

if __name__ == '__main__':
    app()
