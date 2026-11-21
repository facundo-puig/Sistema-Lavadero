
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UsuarioLoginSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    rol = serializers.CharField()


class LoginRespuestaSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    usuario = UsuarioLoginSerializer()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RegistroSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        Usuario = get_user_model()
        email = value.strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este email.'
            )

        return email

    def validate(self, attrs):
        Usuario = get_user_model()

        usuario = Usuario(
            username=attrs['email'],
            email=attrs['email'],
            first_name=attrs['nombre'],
        )

        try:
            validate_password(attrs['password'], user=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'password': error.messages
            }) from error

        return attrs


class RegistroRespuestaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nombre = serializers.CharField()
    email = serializers.EmailField()
    rol = serializers.CharField()



class UsuarioAdministracionSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='first_name')

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'nombre',
            'email',
            'rol',
            'is_active',
        ]
        read_only_fields = fields


class CrearUsuarioAdministracionSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    rol = serializers.ChoiceField(
        choices=['OPERARIO', 'ADMINISTRADOR']
    )

    def validate_email(self, value):
        Usuario = get_user_model()
        email = value.strip().lower()

        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                'Ya existe un usuario con este email.'
            )

        return email

    def validate(self, attrs):
        Usuario = get_user_model()

        usuario = Usuario(
            username=attrs['email'],
            email=attrs['email'],
            first_name=attrs['nombre'],
            rol=attrs['rol'],
        )

        try:
            validate_password(attrs['password'], user=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                'password': error.messages
            }) from error

        return attrs


class CambiarRolSerializer(serializers.Serializer):
    rol = serializers.ChoiceField(
        choices=['CLIENTE', 'OPERARIO', 'ADMINISTRADOR']
    )
