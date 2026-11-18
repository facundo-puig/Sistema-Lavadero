
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