from typing import Annotated, List, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from sqlmodel import asc, desc, select

from app.api.dependencies import get_async_session
from app.models.address_model import Address
from app.models.category_model import Category
from app.models.enums.listing_status import ListingStatus
from app.models.listing_image import ListingImage
from app.models.listing_model import Listing
from app.schemas.listing_schema import (
    ListingCardCreate,
    ListingCardDetails,
    ListingCardProfile,
    ListingCreate,
    ListingUpdate,
    SellerInfoCard,
    listingQueryParameters,
)
from app.services.listing.listing_service import ListingService
from app.services.user.user_service import UserService

router = APIRouter()


# TODO: change this so that pictures can be uploaded, change response model, and change ListingCreate schema to take pictures
# TESTED for listing creation
# create listing
@router.post(
    "/",
    response_model=ListingCardDetails,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing",
    description="Creates a listing with optional address and category assignments. Requires a valid seller ID.",
)
async def create_listing(
    *,
    new_listing_data: ListingCreate,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that address exists
    if new_listing_data.address_id:
        address = await session.get(Address, new_listing_data.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {new_listing_data.address_id} not found.",
            )

    # check that categories exist and collect them
    category_objs = []
    if new_listing_data.category_ids:
        for category_id in new_listing_data.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )
            category_objs.append(category)

    # create listing instance
    listing = Listing(
        title=new_listing_data.title,
        description=new_listing_data.description,
        price=new_listing_data.price,
        listing_status=new_listing_data.listing_status,
        offer_type=new_listing_data.offer_type,
        address=address,
        seller=current_user,
        categories=category_objs,
    )

    image_paths: list[str] = []
    for image_path in new_listing_data.image_paths:
        listing.images.append(ListingImage(path=image_path))
        image_paths.append(image_path)

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)

    seller_rating = await user_service.get_seller_rating(listing.seller_id)

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        # liked=listing in current_user.favorite_listings,
        liked=False,
        seller=SellerInfoCard(
            id=current_user.id,
            firstname=current_user.firstname,
            lastname=current_user.lastname,
            rating=seller_rating,
        ),
        address=address,
        categories=category_objs,
        # HAVE TO USE THE OBJECTS, OTHERWISE IT WILL TRY TO LAZY LOAD IT FROM listings AND FAIL
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        image_paths=image_paths,
    )

    return response


# TESTED for getting listings of user that has listings
# TODO: add test for user that has no listings
# get current user's listings in profile/listings
@router.get(
    "/my-listings",
    response_model=List[ListingCardProfile],
    summary="Get current user's listings",
    description="Fetch all listings created by the current user.",
)
async def get_my_listings(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    listing_service: ListingService = Depends(ListingService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # return only posted listings that are not removed
    result = await session.execute(
        select(Listing)
        .where(Listing.seller_id == current_user.id)
        .where(Listing.listing_status != ListingStatus.REMOVED)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.images),
        )
    )

    listings: list[Listing] = result.scalars().all()
    listing_result: list[ListingCardProfile] = []
    for listing in listings:
        presigned_urls = listing_service.get_presigned_urls(listing.images)
        listing_data = listing.model_dump(exclude_none=True)
        # set title image
        main_image = presigned_urls[0] if len(presigned_urls) > 0 else ""
        listing_data.setdefault("image_path", main_image)

        listing_data.setdefault("address", listing.address)

        listing_card = ListingCardProfile.model_validate(listing_data)
        listing_result.append(listing_card)

    return listing_result


# TESTED for using limit, offset, offer_types, listing_status
# get listings with specific categories, price, status, offer type, and (address)
@router.get(
    "/",
    response_model=List[ListingCardDetails],
    summary="Filter and list listings",
    description="Retrieve listings by categories, price range, offer type, .... Listings with status REMOVED are excluded.",
)
async def get_listings_by_params(
    *,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    params: Annotated[listingQueryParameters, Depends()],
    listing_service: ListingService = Depends(ListingService.get_dependency),
):
    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    # check that categories exists
    if params.category_ids:
        for category_id in params.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )

    # LISTING STATUS FROM FRONTEND CANNOT BE REMOVED
    if params.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Listing status cannot be REMOVED when filtering listings.",
        )

    # Get the rating subquery from user_service
    rating_subquery = user_service.get_seller_rating_subquery()

    rating_expr = func.coalesce(rating_subquery.c.avg_rating, 0).label("seller_rating")

    # build query
    query = (
        select(Listing, rating_expr)
        .outerjoin(
            rating_subquery,
            rating_subquery.c.seller_id == Listing.seller_id,
        )
        .options(
            selectinload(Listing.seller),
            selectinload(Listing.categories),
            selectinload(Listing.address),
            selectinload(Listing.images),
        )
        .where(Listing.listing_status == ListingStatus.ACTIVE)  # only active listings
    )

    # Filtering:
    if params.category_ids:
        query = query.where(
            Listing.categories.any(Category.id.in_(params.category_ids))
        )
    if params.offer_type:
        query = query.where(Listing.offer_type == params.offer_type)
    if params.listing_status:
        query = query.where(Listing.listing_status == params.listing_status)
    if params.min_price:
        query = query.where(Listing.price >= params.min_price)
    if params.max_price:
        query = query.where(Listing.price <= params.max_price)
    if params.search:
        query = query.where(Listing.title.ilike(f"%{params.search}%"))
    if params.min_rating:
        query = query.where(rating_expr >= params.min_rating)

    # Sorting:
    # TODO: sort by location
    sort_columns = {
        "created_at": Listing.created_at,
        "updated_at": Listing.updated_at,
        "price": Listing.price,
        "rating": rating_expr,
    }

    if params.sort_order == "asc":
        query = query.order_by(
            asc(sort_columns.get(params.sort_by, Listing.updated_at))
        )
    else:
        query = query.order_by(
            desc(sort_columns.get(params.sort_by, Listing.updated_at))
        )

    # Pagination:
    query = query.limit(params.limit).offset(params.offset)

    # Execute the query
    listings = await session.execute(query)
    listings: Tuple[Listing, int] = listings.all()

    output_listings: List[ListingCardDetails] = []

    # Iterate through the results and create the response
    for listing, seller_rating in listings:
        seller_rating = round(seller_rating, 2) if seller_rating else None
        presigned_urls = listing_service.get_presigned_urls(listing.images)
        output_listings.append(
            ListingCardDetails(
                id=listing.id,
                title=listing.title,
                description=listing.description,
                price=listing.price,
                listing_status=listing.listing_status,
                offer_type=listing.offer_type,
                liked=listing in current_user.favorite_listings,
                seller=SellerInfoCard(
                    id=listing.seller.id,
                    firstname=listing.seller.firstname,
                    lastname=listing.seller.lastname,
                    rating=seller_rating,
                ),
                address=listing.address,
                categories=listing.categories,
                created_at=listing.created_at,
                updated_at=listing.updated_at,
                image_paths=presigned_urls,
            )
        )

    return output_listings


# TESTED for getting specific listing by id
# get specific listing by id
@router.get(
    "/{listing_id}",
    response_model=ListingCardDetails,
    summary="Get a listing by ID",
    description="Fetch a specific listing by ID unless its status is REMOVED.",
)
async def get_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    listing_service: ListingService = Depends(ListingService.get_dependency),
):
    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    result = await session.execute(
        select(Listing)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.images),
        )
        .where(Listing.id == listing_id)
    )
    listing = result.scalars().one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that listing is not removed
    if listing.listing_status == ListingStatus.REMOVED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} has been removed.",
        )
    seller_rating = await user_service.get_seller_rating(listing.seller_id)

    # generate presigned urls for listing images
    presigned_urls = listing_service.get_presigned_urls(listing.images)

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=listing in current_user.favorite_listings,
        seller=SellerInfoCard(
            id=listing.seller.id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=seller_rating,
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        image_paths=presigned_urls,
    )

    return response


# TESTED title, description, price, listing_status, offer)type, address_id, category_ids
# update listing
@router.put(
    "/{listing_id}",
    response_model=ListingCardDetails,
    summary="Update an existing listing",
    description="Updates listing fields and category relationships. You must provide valid address/category IDs.",
)
async def update_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
    updated_listing_data: ListingUpdate,
    listing_service: ListingService = Depends(ListingService.get_dependency),
):
    current_user = await user_service.get_current_user(
        dependencies=["favorite_listings"]
    )

    # check that listing exists
    result = await session.execute(
        select(Listing)
        .options(
            selectinload(Listing.address),
            selectinload(Listing.categories),
            selectinload(Listing.seller),
            selectinload(Listing.images),
        )
        .where(Listing.id == listing_id)
        .where(Listing.listing_status != ListingStatus.REMOVED)
    )

    listing = result.scalars().one_or_none()

    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found",
        )

    # TEMP NEEDS TO BE HERE AS updated_at will be marked as expired and lazy loaded otherwise
    temp = listing.updated_at

    # check that user is logged in and is the seller of the listing
    if current_user.id != listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this listing.",
        )

    # check that address exists
    if updated_listing_data.address_id is not None:
        address = await session.get(Address, updated_listing_data.address_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with ID {updated_listing_data.address_id} not found.",
            )

        listing.address = address

    # check that categories exist
    if updated_listing_data.category_ids:
        category_objs = []
        for category_id in updated_listing_data.category_ids:
            category = await session.get(Category, category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with ID {category_id} not found.",
                )
            category_objs.append(category)

        listing.categories = category_objs

    # update listing instance
    update_data = updated_listing_data.model_dump(
        exclude_unset=True, exclude={"category_ids"}
    )

    for key, value in update_data.items():
        setattr(listing, key, value)

    # if updated_listing_data.image_paths and len(updated_listing_data.image_paths) > 0:
    #     # TODO: update image paths:
    #     listing.images = updated_listing_data.image_paths

    seller_rating = await user_service.get_seller_rating(listing.seller_id)
    presigned_urls = listing_service.get_presigned_urls(listing.images)

    response = ListingCardDetails(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        listing_status=listing.listing_status,
        offer_type=listing.offer_type,
        liked=listing in current_user.favorite_listings,
        seller=SellerInfoCard(
            id=listing.seller.id,
            firstname=listing.seller.firstname,
            lastname=listing.seller.lastname,
            rating=seller_rating,
        ),
        address=listing.address,
        categories=listing.categories,
        created_at=listing.created_at,
        updated_at=temp,
        image_paths=presigned_urls,
    )

    # add listing to DB session
    session.add(listing)
    await session.commit()
    await session.refresh(listing)

    return response


# TESTED removing
# delete listing
@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a listing",
    description="Marks the listing as REMOVED. It will no longer be visible to users.",
)
async def delete_listing(
    *,
    listing_id: int,
    session: AsyncSession = Depends(get_async_session),
    user_service: UserService = Depends(UserService.get_dependency),
):
    current_user = await user_service.get_current_user()

    # check that listing exists
    listing = await session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing with ID {listing_id} not found.",
        )

    # check that user is logged in and is the seller of the listing
    if current_user.id != listing.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this listing.",
        )

    # set listing status to removed
    listing.listing_status = ListingStatus.REMOVED
    session.add(listing)
    await session.commit()
    await session.refresh(listing)
    return listing
