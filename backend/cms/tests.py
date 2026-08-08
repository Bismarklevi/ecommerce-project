import io

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .models import Banner

User = get_user_model()


def make_test_image(name="banner.jpg"):
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color="green").save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


class AdminBannerUploadTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(username="staff", email="s@example.com", password="pw")
        self.client.force_login(self.staff)

    def test_banner_image_uploaded_via_admin_reaches_storage_and_api(self):
        # See the docstring on products.tests.AdminImageUploadTests for why
        # this checks storage + the API's URL rather than fetching the URL
        # over HTTP.
        response = self.client.post(
            "/admin/cms/banner/add/",
            {
                "title": "New Season", "subtitle": "Shop now", "image": make_test_image(),
                "link_url": "/products", "position": "0", "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        banner = Banner.objects.get(title="New Season")
        self.assertTrue(banner.image)
        self.assertTrue(default_storage.exists(banner.image.name))

        api_response = self.client.get("/api/banners/")
        payload = next(row for row in api_response.json()["results"] if row["title"] == "New Season")
        self.assertTrue(payload["image"].startswith("http"))
        self.assertIn("cms/banners/", payload["image"])

    def test_inactive_banner_does_not_appear_in_public_api(self):
        self.client.post(
            "/admin/cms/banner/add/",
            {
                "title": "Hidden Banner", "subtitle": "", "image": make_test_image("hidden.jpg"),
                "link_url": "", "position": "0", "is_active": "",
            },
            follow=True,
        )
        api_response = self.client.get("/api/banners/")
        titles = [row["title"] for row in api_response.json()["results"]]
        self.assertNotIn("Hidden Banner", titles)
