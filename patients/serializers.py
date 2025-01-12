from rest_framework import serializers

from .models import Patient, Treatment, TreatmentPlan


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'surname', 'age']


class TreatmentListSerializer(serializers.ModelSerializer):
    doctor = serializers.SerializerMethodField()
    class Meta:
        model = Treatment 
        fields = ['id', 'doctor', 'patient', 'date', 'tooth']

    def get_doctor(self, obj):
        return f'{obj.doctor.name} {obj.doctor.surname}'
    

class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ['event', 'patient', 'doctor', 'date', 'duration', 'tooth', 'anesthesia', 'details']


class TreatmentPlanSerializer(serializers.ModelSerializer):
    treatments = TreatmentSerializer(many=True, required=False, read_only=True)
    class Meta:
        model = TreatmentPlan
        fields = ['id', 'name', 'description', 'patient' ,'treatments']