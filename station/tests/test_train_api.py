import tempfile

from PIL import Image
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.db.models import Count

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Train, TrainType, Carriage
from station.serializers import TrainListSerializer

TRAIN_URL = reverse("station:train-list")


def train_detail_url(train_id):
    """Return train detail URL"""
    return reverse("station:train-detail", args=[train_id])


def sample_train_type(**params):
    """Create and return a sample train type"""
    defaults = {
        "name": "express",
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def sample_train(**params):
    """Create and return a sample train"""
    defaults = {
        "name": "Sample train",
        "number": "123",
        "train_type": sample_train_type(),
    }
    defaults.update(params)

    return Train.objects.create(**defaults)


def sample_carriage(**params):
    """Create and return a sample carriage"""
    defaults = {
        "number": "1",
        "seats": 20,
        "carriage_type": Carriage.CarriageType.ECONOMY,
    }
    defaults.update(params)

    return Carriage.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for train image upload"""
    return reverse("station:train-upload-image", args=[train_id])


class AdminTrainApiTest(TestCase):
    def setUp(self):
        """Set up test client and create admin user"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com", password="testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train(self):
        """Test creating a new train"""
        payload = {
            "name": "Sample train",
            "number": "123",
            "train_type": sample_train_type().id,
        }
        res = self.client.post(TRAIN_URL, payload)
        train = Train.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload.keys():
            if key == "train_type":
                self.assertEqual(payload[key], getattr(train, key).id)
            else:
                self.assertEqual(payload[key], getattr(train, key))

    def test_delete_train_not_allowed(self):
        """Test deleting a train"""
        train = sample_train()
        url = train_detail_url(train.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AuthenticatedTrainApiTest(TestCase):
    def setUp(self) -> None:
        """Set up test client and create objects needed for tests"""

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="test@test.com", password="testpass", is_staff=False
        )
        self.client.force_authenticate(self.user)

        # Objects needed for tests
        self.train_type1 = sample_train_type(name="express")
        self.train_type2 = sample_train_type(name="ordinary")
        self.train_type3 = sample_train_type(name="hight-speed")

        self.train1 = sample_train(
            name="sample train 1", number="111", train_type=self.train_type1
        )
        self.train2 = sample_train(
            name="sample train 2", number="222", train_type=self.train_type2
        )
        self.train3 = sample_train(
            name="sample3 train 3", number="333", train_type=self.train_type3
        )

        sample_carriage(number="1", train=self.train1)
        sample_carriage(number="2", train=self.train2)
        sample_carriage(number="3", train=self.train2)

        self.payload = {
            "name": "Sample train",
            "number": "123",
            "train_type": sample_train_type().id,
        }

        self.trains = (
            Train.objects.all()
            .order_by("-id")
            .annotate(carriage_count=Count("carriages"))
        )
        self.serializer1 = TrainListSerializer(self.trains.get(id=self.train1.id))
        self.serializer2 = TrainListSerializer(self.trains.get(id=self.train2.id))
        self.serializer3 = TrainListSerializer(self.trains.get(id=self.train3.id))

    def test_create_train_forbidden(self):
        """Test creating a new train"""
        res = self.client.post(TRAIN_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_trains(self):
        """Test retrieving a list of trains"""
        res = self.client.get(TRAIN_URL)

        serializer = TrainListSerializer(self.trains, many=True)

        res_data_sorted = sorted(res.data, key=lambda x: x["id"])
        serializer_data_sorted = sorted(serializer.data, key=lambda x: x["id"])

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res_data_sorted, serializer_data_sorted)

    def test_retrieve_train_detail(self):
        """Test retrieving a train"""
        url = train_detail_url(self.train1.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.train1.id)

    def test_filter_train_by_number(self):
        """Test filtering trains by number"""
        res = self.client.get(TRAIN_URL, {"number": "222"})

        self.assertIn(self.serializer2.data, res.data)
        self.assertNotIn(self.serializer1.data, res.data)
        self.assertNotIn(self.serializer3.data, res.data)

    def test_filter_train_by_train_type(self):
        """Test filtering trains by train type name"""
        res = self.client.get(TRAIN_URL, {"train_type_name": self.train_type2.name})

        self.assertIn(self.serializer2.data, res.data)
        self.assertNotIn(self.serializer1.data, res.data)
        self.assertNotIn(self.serializer3.data, res.data)

    def test_filter_train_by_name(self):
        """Test filtering trains by name"""
        res = self.client.get(TRAIN_URL, {"name": "sample train 1"})

        self.assertIn(self.serializer1.data, res.data)
        self.assertNotIn(self.serializer2.data, res.data)
        self.assertNotIn(self.serializer3.data, res.data)


class UnauthenticatedTrainApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class TrainImageUploadTests(TestCase):
    def setUp(self):
        """Set up admin user and create objects needed for tests"""
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com", password="testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.train_type = sample_train_type(name="express")
        self.train = sample_train(
            name="sample train 1", number="111", train_type=self.train_type
        )

        sample_carriage(number="1", train=self.train)
        sample_carriage(number="2", train=self.train)

    def tearDown(self):
        """Clean up files after tests"""
        self.train.image.delete()

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_image_to_train(self):
        """Test uploading an image to train"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.train.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(self.train.image)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_url(self.train.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_post_image_to_train_list_should_not_work(self):
        """Test that posting image to train list should not work"""
        url = TRAIN_URL
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {
                    "name": "Train",
                    "number": "000",
                    "train_type": sample_train_type().id,
                    "image": ntf,
                },
                format="multipart",
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(name="Train")
        self.assertFalse(train.image)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_image_url_is_shown_on_train_detail(self):
        """Test that image url is shown on train detail"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")

        url = train_detail_url(self.train.id)
        res = self.client.get(url)

        self.assertIn("image", res.data)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_image_url_is_shown_on_train_list(self):
        """Test that image url is shown on train list"""
        url = image_upload_url(self.train.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")

        url = TRAIN_URL
        res = self.client.get(url)

        self.assertIn("image", res.data[0])
