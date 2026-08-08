from rest_framework import serializers

from .models import Banner, ContentBlock


class BannerSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Banner
        fields = ["id", "title", "subtitle", "image", "link_url", "position"]

    def get_image(self, obj):
        request = self.context.get("request")
        url = obj.image.url if obj.image else ""
        if url and request is not None:
            return request.build_absolute_uri(url)
        return url


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ["key", "title", "body"]
