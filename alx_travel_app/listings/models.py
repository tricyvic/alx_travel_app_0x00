import uuid
from django.db import models
from django.conf import settings # Used to reference the AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator

# --- Listing Model ---
class Listing(models.Model):
    """
    Represents a property listed for rent by a host.
    """
    listing_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, # Primary Key, UUID, automatically indexed
        editable=False,      # Value cannot be changed after creation
        unique=True,         # Ensures uniqueness
        db_index=True        # Explicitly indexed for faster lookups (though PK implies indexing)
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Foreign Key, references User(user_id)
        on_delete=models.CASCADE, # If a host is deleted, their listings are also deleted
        related_name='listings_hosted', # Name for the reverse relation from User to Listing
        null=False # NOT NULL constraint
    )
    name = models.CharField(max_length=255, null=False) # VARCHAR, NOT NULL
    description = models.TextField(null=False) # TEXT, NOT NULL
    location = models.CharField(max_length=255, null=False) # VARCHAR, NOT NULL
    pricepernight = models.DecimalField(
        max_digits=10,       # Maximum total digits (e.g., 99999999.99)
        decimal_places=2,    # Number of decimal places
        null=False           # NOT NULL constraint
    )
    created_at = models.DateTimeField(
        auto_now_add=True    # Automatically sets the creation timestamp
    )
    updated_at = models.DateTimeField(
        auto_now=True        # Automatically updates the timestamp on each save
    )

    class Meta:
        """
        Meta options for the Listing model.
        """
        verbose_name = "Listing"
        verbose_name_plural = "Listings"
        ordering = ['-created_at'] # Default ordering: newest listings first

    def __str__(self):
        """
        Returns a human-readable string representation of the Listing object.
        """
        return f"{self.name} in {self.location} by {self.host.username if hasattr(self.host, 'username') else self.host.email}"


# --- Booking Model ---

# Define choices for the 'status' field
BOOKING_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('canceled', 'Canceled'),
]

class Booking(models.Model):
    """
    Represents a booking made by a user for a specific listing.
    """
    booking_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, # Primary Key, UUID, automatically indexed
        editable=False,
        unique=True,
        db_index=True        # Explicitly indexed
    )
    listing = models.ForeignKey(
        Listing,             # Foreign Key, references Listing(listing_id)
        on_delete=models.CASCADE, # If a listing is deleted, its bookings are also deleted
        related_name='bookings', # Name for the reverse relation from Listing to Booking
        null=False # NOT NULL constraint
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Foreign Key, references User(user_id)
        on_delete=models.CASCADE, # If a user is deleted, their bookings are also deleted
        related_name='bookings_made', # Name for the reverse relation from User to Booking
        null=False # NOT NULL constraint
    )
    start_date = models.DateField(null=False) # DATE, NOT NULL
    end_date = models.DateField(null=False)   # DATE, NOT NULL
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=False # NOT NULL constraint
    )
    status = models.CharField(
        max_length=10,
        choices=BOOKING_STATUS_CHOICES, # ENUM constraint (Django CharField with choices)
        default='pending',              # DEFAULT value
        null=False                      # NOT NULL constraint
    )
    created_at = models.DateTimeField(
        auto_now_add=True # TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
    )

    class Meta:
        """
        Meta options for the Booking model.
        """
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-created_at'] # Default ordering: newest bookings first
        # Optional: Add a unique constraint to prevent double-booking the same listing by the same user on the same dates
        # This can be complex for date ranges and might require custom validation or database triggers for strict enforcement.
        # For exact date conflicts: unique_together = ('listing', 'start_date', 'end_date')

    def __str__(self):
        """
        Returns a human-readable string representation of the Booking object.
        """
        return f"Booking {self.booking_id.hex[:8]} for {self.listing.name} by {self.user.username if hasattr(self.user, 'username') else self.user.email}"


# --- Review Model ---
class Review(models.Model):
    """
    Represents a review given by a user for a specific listing.
    """
    review_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, # Primary Key, UUID, automatically indexed
        editable=False,
        unique=True
    )
    listing = models.ForeignKey(
        Listing,             # Foreign Key, references Listing(listing_id)
        on_delete=models.CASCADE, # If a listing is deleted, its reviews are also deleted
        related_name='reviews', # Name for the reverse relation from Listing to Review
        null=False # NOT NULL constraint
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Foreign Key, references User(user_id)
        on_delete=models.CASCADE, # If a user is deleted, their reviews are also deleted
        related_name='reviews_written', # Name for the reverse relation from User to Review
        null=False # NOT NULL constraint
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], # CHECK constraint: rating must be between 1 and 5
        null=False # NOT NULL constraint
    )
    comment = models.TextField(null=False) # TEXT, NOT NULL
    created_at = models.DateTimeField(
        auto_now_add=True # TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
    )

    class Meta:
        """
        Meta options for the Review model.
        """
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ['-created_at'] # Default ordering: newest reviews first
        # Optional: Ensure a user can only review a specific listing once
        unique_together = ('listing', 'user')

    def __str__(self):
        """
        Returns a human-readable string representation of the Review object.
        """
        return f"Review for {self.listing.name} by {self.user.username if hasattr(self.user, 'username') else self.user.email} - Rating: {self.rating}"