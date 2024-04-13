from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q

# Create your views here.
def home_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'index.html')

def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'adminclick.html')

def doctorclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'doctorclick.html')

def patientclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'patientclick.html')



def admin_signup_view(request):
    form=forms.AdminSigupForm()
    if request.method=='POST':
        form=forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.set_password(user.password)
            user.save()
            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)
            return HttpResponseRedirect('adminlogin')
    return render(request,'adminsignup.html',{'form':form})




def doctor_signup_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST,request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor=doctor.save()
            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)
        return HttpResponseRedirect('doctorlogin')
    return render(request,'doctorsignup.html',context=mydict)


def patient_signup_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.user=user
            patient=patient.save()
            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)
        return HttpResponseRedirect('patientlogin')
    return render(request,'patientsignup.html',context=mydict)




def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_doctor(request.user):
            return redirect('doctor-dashboard')
    elif is_patient(request.user):
            return redirect('patient-dashboard')
    else:
        error_message = "Invalid username or password. Please try again."
        return render(request, 'index.html', {'error_message': error_message})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    doctors=models.Doctor.objects.all().order_by('-id')
    patients=models.Patient.objects.all().order_by('-id')
    doctorcount=models.Doctor.objects.all().filter(status=True).count()
    patientcount=models.Patient.objects.all().filter(status=True).count()
   
    mydict={
    'doctors':doctors,
    'patients':patients,
    'doctorcount':doctorcount,
    'patientcount':patientcount,
    
    }
    return render(request,'admin_dashboard.html',context=mydict)

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    #for three cards
   

    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'doctor_dashboard.html',context=mydict)

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id)
    mydict={
    'patient':patient,
    'symptoms':patient.symptoms,
    'admitDate':patient.admitDate,
    }
    return render(request,'patient_dashboard.html',context=mydict)




@login_required
def patient_dashboard(request):
    patient = request.user.patient
    appointments = Appointment.objects.filter(patient=patient, status__in=['Pending', 'Confirmed'])
    context = {'appointments': appointments}
    return render(request, 'patientdashboard.html', context)

@login_required
def request_appointment(request):
    if request.method == 'POST':
        form = RequestAppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user.patient
            appointment.save()
            return redirect('patient_dashboard')  # Redirect to patient dashboard after successful request
    else:
        form = RequestAppointmentForm()
    context = {'form': form}
    return render(request, 'request_appointment.html', context)

@login_required
def manage_medications(request):
    patient = request.user.patient
    if request.method == 'POST':
        form = MedicationManagementForm(request.POST)
        if form.is_valid():
            medication = form.save(commit=False)
            if medication.patient is None:  # If a new medication is added
                medication.patient = patient
            medication.save()
            return redirect('manage_medications')  # Redirect back to manage medications after saving
    else:
        form = MedicationManagementForm(initial={'patient': patient})  # Pre-populate patient field
    medications = Medication.objects.filter(patient=patient)  # Filter medications for this patient
    context = {'form': form, 'medications': medications}
    return render(request, 'manage_medications.html', context)

@login_required
def request_medical_records(request):
    if request.method == 'POST':
        form = MedicalRecordRequestForm(request.POST)
        if form.is_valid():
            # Handle medical record request logic here (e.g., send notification to doctor)
            return redirect('patient_dashboard')  # Redirect back to patient dashboard after request
    else:
        form = MedicalRecordRequestForm()
    context = {'form': form}
    return render(request, 'request_medical_records.html', context)


