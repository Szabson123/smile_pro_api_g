from rest_framework import serializers

from .models import Patient, Treatment, TreatmentPlan, Teeth, TeethInfo


class TeethInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeethInfo
        fields = ['problem']

class TeethSerializer(serializers.ModelSerializer):
    info = TeethInfoSerializer(many=True)
    class Meta:
        model = Teeth
        fields = ['name', 'info']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'surname', 'age']


class TreatmentListSerializer(serializers.ModelSerializer):
    doctor = serializers.SerializerMethodField()
    teeth = TeethSerializer(many=True, read_only=True)
    class Meta:
        model = Treatment 
        fields = ['id', 'doctor', 'patient', 'date', 'teeth']

    def get_doctor(self, obj):
        return f'{obj.doctor.name} {obj.doctor.surname}'

class TreatmentSerializer(serializers.ModelSerializer):
    teeth = TeethSerializer(many=True, required=False) 
    class Meta:
        model = Treatment
        fields = ['event', 'patient', 'doctor', 'date', 'duration', 'anesthesia', 'details', 'teeth']

    def create(self, validated_data):
        teeth_data = validated_data.pop('teeth', [])

        treatment = Treatment.objects.create(**validated_data)

        for tooth_data in teeth_data:
            info_data = tooth_data.pop('info', [])

            tooth, created = Teeth.objects.get_or_create(
                patient=treatment.patient,
                name=tooth_data['name'],
                defaults={'treatment': treatment}
            )

            if not created:
                tooth.treatment = treatment
                tooth.save()

            for info in info_data:
                TeethInfo.objects.create(teeth=tooth, **info)

        return treatment

    def update(self, instance, validated_data):
        teeth_data = validated_data.pop('teeth', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for tooth_data in teeth_data:
            info_data = tooth_data.pop('info', [])

            tooth, created = Teeth.objects.get_or_create(
                patient=instance.patient,
                name=tooth_data['name'],
                defaults={'treatment': instance}
            )

            if not created:
                tooth.treatment = instance
                tooth.save()

            for info in info_data:
                TeethInfo.objects.create(teeth=tooth, **info)

        return instance


class TreatmentPlanSerializer(serializers.ModelSerializer):
    treatments = TreatmentSerializer(many=True, required=False, read_only=True)
    class Meta:
        model = TreatmentPlan
        fields = ['id', 'name', 'description', 'patient' ,'treatments']