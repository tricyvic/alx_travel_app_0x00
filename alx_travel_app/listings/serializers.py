from rest_framework import serializers
from .models import Listing, Booking, Review # Import your models
from django.conf import settings # To reference AUTH_USER_MODEL

# If you are using Django's built-in User model, uncomment the line below
# and comment out 'from .models import User' if it's not defined in models.py
# from django.contrib.auth import get_user_model
# User = get_user_model()
# Otherwise, ensure your custom User model is imported or accessible.
# Assuming User is in listings/models.py for this example:
from .models import User


# --- Helper Serializers for Nested Relationships ---

class SimpleUserSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for User, used when nesting User objects
    to prevent excessive data or circular dependencies.
    """
    class Meta:
        model = User
        # Adjust fields based on what minimal user info you want to expose when nested
        fields = ['user_id', 'first_name', 'last_name', 'email']
        read_only_fields = ['user_id', 'first_name', 'last_name', 'email']


class SimpleListingSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for Listing, used when nesting Listing objects
    (e.g., within Booking) to prevent excessive data or circular dependencies.
    """
    class Meta:
        model = Listing
        fields = ['listing_id', 'name', 'location', 'pricepernight']
        read_only_fields = ['listing_id', 'name', 'location', 'pricepernight']


# --- Main Serializers ---

class ListingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Listing model.
    Includes nested representation of the host.
    """
    # Nested representation for the host.
    # This will display the details of the User object instead of just their ID.
    host = SimpleUserSerializer(read_only=True)

    # Write-only field for setting the host by their user_id (UUID).
    # This is used when sending POST/PUT requests to create/update a listing.
    host_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), # Ensure the queryset is correct for your User model
        source='host',               # This tells DRF to map 'host_id' to the 'host' field
        write_only=True,             # This field is only for input, not output
        required=True                # Host is a required field for a listing
    )

    # Optional: Add a SerializerMethodField to get average rating for a listing
    average_rating = serializers.SerializerMethodField()

    def get_average_rating(self, obj):
        """
        Calculates the average rating for a listing based on its reviews.
        """
        # Ensure 'Review' model is imported if you uncomment this
        # from .models import Review # Or ensure Review is imported at the top
        reviews = obj.reviews.all() # Access related reviews via the related_name
        if reviews.exists():
            return round(sum(review.rating for review in reviews) / reviews.count(), 2)
        return None # Or 0.0, depending on desired representation for no reviews

    class Meta:
        model = Listing
        fields = [
            'listing_id',
            'host',          # Read-only nested host object
            'name',
            'description',
            'location',
            'pricepernight',
            'created_at',
            'updated_at',
            'average_rating', # Include the calculated average rating
            'host_id'        # Write-only field for setting host by ID
        ]
        read_only_fields = ['listing_id', 'created_at', 'updated_at']


class BookingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Booking model.
    Includes nested representation of the listing and the user who made the booking.
    """
    # Nested representation for the listing.
    # Using SimpleListingSerializer to avoid deep nesting.
    listing = SimpleListingSerializer(read_only=True)

    # Nested representation for the user who made the booking.
    user = SimpleUserSerializer(read_only=True)

    # Write-only fields for setting relationships by their UUIDs.
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(),
        source='listing',
        write_only=True,
        required=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), # Ensure the queryset is correct for your User model
        source='user',
        write_only=True,
        required=True
    )

    class Meta:
        model = Booking
        fields = [
            'booking_id',
            'listing',      # Read-only nested listing object
            'user',         # Read-only nested user object
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_at',
            'listing_id',   # Write-only field for setting listing by ID
            'user_id'       # Write-only field for setting user by ID
        ]
        read_only_fields = ['booking_id', 'created_at', 'total_price'] # Total price is usually calculated by backend

    # Optional: Add validation for start_date < end_date
    def validate(self, data):
        """
        Check that the start date is before the end date.
        """
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        return data

    # Optional: Override create to calculate total_price before saving
    def create(self, validated_data):
        # Calculate total_price before saving the booking
        listing = validated_data['listing']
        start_date = validated_data['start_date']
        end_date = validated_data['end_date']

        # Calculate number of nights
        num_nights = (end_date - start_date).days
        if num_nights <= 0:
            raise serializers.ValidationError("Booking must be for at least one night.")

        validated_data['total_price'] = listing.pricepernight * num_nights
        return super().create(validated_data)