import os
from uuid import UUID, uuid4
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status

from app.models.company_models import (
    CompanyBankDetailsModel,
    CompanyModel,
    CompanyAddressModel,
    CompanyDocumentModel,
)
from app.models.industry_skill_models import IndustryTypeModel
from app.schemas.company_schema import (
    CompanyAddressCreateSchema,
    CompanyBankDetailsSchema,
    CompanyDocumentCreateSchema,
    CompanyInfoSchema,
    CompanyProfileDetailsSchema,
    CompanyProfileUpdateSchema,
    ContactInfoSchema,
    DocumentInfoSchema,
    LogoUpdateSchema,
)

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point


# -----------------------Company profile exist or not Service ----------------------- #
def company_profile_exist_service(
    firebase_uid: str,
    db: Session,
) -> CompanyModel | None:

    return (
        db.query(CompanyModel).filter(CompanyModel.firebase_uid == firebase_uid).first()
    )


# -----------------------End Company profile exist or not Service ----------------------- #


# -----------------------Get Company Profile Service ----------------------- #
def get_company_profile_service(
    firebase_uid: str,
    db: Session,
) -> dict:
    try:
        company = (
            db.query(CompanyModel)
            .options(
                selectinload(CompanyModel.addresses),
                # selectinload(CompanyModel.documents),
                selectinload(CompanyModel.bank_details),
            )
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        industry_name = None
        if company.industry_id:
            industry = (
                db.query(IndustryTypeModel.name)
                .filter(IndustryTypeModel.id == company.industry_id)
                .first()
            )
            industry_name = industry[0] if industry else None

        return {
            "id": company.id,
            "firebase_uid": company.firebase_uid,
            "company_name": company.company_name,
            "industry_id": company.industry_id,
            "industry_name": industry_name,
            "gst_number": company.gst_number,
            "auth_phone": company.auth_phone,
            "contact_person_name": company.contact_person_name,
            "contact_phone": company.contact_phone,
            "contact_email": company.contact_email,
            "logo_url": company.logo_url,
            "status": company.status,
            "is_verified": company.is_verified,
            "is_active": company.is_active,
            "addresses": [
                {
                    "id": addr.id,
                    "address": addr.address,
                    "unit_name": addr.unit_name,
                    "city": addr.city,
                    "state": addr.state,
                    "pincode": addr.pincode,
                    "latitude": (to_shape(addr.location).y if addr.location else None),
                    "longitude": (to_shape(addr.location).x if addr.location else None),
                }
                for addr in company.addresses
            ],
            "bank_details": [
                {
                    "bank_name": bank.bank_name,
                    "account_holder_name": bank.account_holder_name,
                    "account_number": bank.account_number,
                    "ifsc_code": bank.ifsc_code,
                    "upi_id": bank.upi_id,
                }
                for bank in company.bank_details
            ],
            "created_at": company.created_at,
            "updated_at": company.updated_at,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("DB ERROR 👉", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching company profile",
        )


# -----------------------End Get Company Profile Service ----------------------- #


# -----------------------Create Company Profile Service----------------------- #
def create_company_profile_service(
    company: CompanyInfoSchema,
    firebase_uid: str,
    db: Session,
) -> CompanyModel:
    try:
        # Validation 1 - Prevent duplicate registration for same firebase_uid
        company_db = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        company_db = CompanyModel(
            firebase_uid=firebase_uid,
            company_name=company.companyName,
            industry_id=company.industryId,
            gst_number=company.gstNo,
            auth_phone=company.authPhone,
        )
        db.add(company_db)
        db.flush()
        for addr in company.addresses:
            location = from_shape(
                Point(addr.longitude, addr.latitude),  # IMPORTANT: lng, lat order
                srid=4326,
            )
            db.add(
                CompanyAddressModel(
                    company_id=company_db.id,
                    address=addr.address,
                    unit_name=addr.unitName,
                    city=addr.city,
                    state=addr.state,
                    pincode=addr.pincode,
                    location=location,  # Store as PostGIS geometry
                )
            )

        return company_db

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database transaction failed",
        )


# -----------------------End Create Company Profile Service----------------------- #


# -----------------------Update Contact Info Service----------------------- #
def update_contact_info_service(
    contact_info: ContactInfoSchema,
    firebase_uid: str,
    db: Session,
) -> CompanyModel:
    try:
        company_profile = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        # Check phone uniqueness across other companies
        if contact_info.contactPersonPhone:
            phone_exists = (
                db.query(CompanyModel)
                .filter(
                    CompanyModel.contact_phone == contact_info.contactPersonPhone,
                    CompanyModel.firebase_uid != firebase_uid,
                )
                .first()
            )
            if phone_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Phone number already registered with another company",
                )

        # Check email uniqueness across other companies
        if contact_info.contactEmail:
            email_exists = (
                db.query(CompanyModel)
                .filter(
                    CompanyModel.contact_email == contact_info.contactEmail,
                    CompanyModel.firebase_uid != firebase_uid,
                )
                .first()
            )
            if email_exists:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered with another company",
                )

        # Update fields (industry standard)
        company_profile.contact_person_name = contact_info.contactPersonName
        company_profile.contact_country_code = contact_info.contactCountryCode
        company_profile.contact_phone = contact_info.contactPersonPhone
        company_profile.contact_email = contact_info.contactEmail

        db.flush()
        return company_profile
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating contact info",
        )


# -----------------------End Update Contact Info Service----------------------- #


# -----------------------Update Document Service----------------------- #
def update_document_info_service(
    document_info: DocumentInfoSchema,
    firebase_uid: str,
    db: Session,
) -> CompanyModel:
    try:
        company_profile = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )
        if not company_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        # Update document info
        company_profile.logo_url = document_info.logoUrl
        for doc in document_info.documents:
            db.add(
                CompanyDocumentModel(
                    company_id=company_profile.id,
                    document_type=doc.documentType,
                    document_url=doc.documentUrl,
                )
            )
            # If document type is IDP is uploaded, set status to unapproved for verification
            if (doc.documentType or "").strip().upper() in {"IDP"}:
                company_profile.status = "unapproved"
                company_profile.status_approval_message_shown = False

        db.flush()
        return company_profile

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating document info",
        )


# -----------------------End Update Document Service----------------------- #


# -----------------------Update Company Profile Service----------------------- #
# def update_company_profile_service(
#     update: CompanyProfileUpdateSchema,
#     firebase_uid: str,
#     db: Session,
# ) -> CompanyModel:
#     try:

#         company = (
#             db.query(CompanyModel)
#             .filter(CompanyModel.firebase_uid == firebase_uid)
#             .first()
#         )

#         if not company:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Company profile not found",
#             )

#         data = update.model_dump(exclude_unset=True)

#         # Simple field updates
#         if "companyName" in data:
#             company.company_name = data["companyName"]

#         if "industryType" in data:
#             company.industry = data["industryType"]

#         if "gstNo" in data:
#             company.gst_number = data["gstNo"]

#         # Address update (replace strategy)
#         if "addresses" in data:
#             db.query(CompanyAddressModel).filter(
#                 CompanyAddressModel.company_id == company.id
#             ).delete(synchronize_session=False)

#             for addr in data["addresses"]:
#                 location = from_shape(
#                     Point(
#                         addr["longitude"], addr["latitude"]
#                     ),  # IMPORTANT: lng, lat order
#                     srid=4326,
#                 )
#                 db.add(
#                     CompanyAddressModel(
#                         company_id=company.id,
#                         address=addr["address"],
#                         unit_name=addr["unitName"],
#                         city=addr["city"],
#                         state=addr["state"],
#                         pincode=addr["pincode"],
#                         location=location,  # Store as PostGIS geometry
#                     )
#                 )
#         # Contact Info update
#         if "contactInfo" in data:
#             ci = data["contactInfo"]

#             if "contactPersonName" in ci:
#                 company.contact_person_name = ci["contactPersonName"]

#             if "contactPersonPhone" in ci:
#                 company.contact_phone = ci["contactPersonPhone"]

#             if "contactEmail" in ci:
#                 exists = (
#                     db.query(CompanyModel)
#                     .filter(
#                         CompanyModel.contact_email == ci["contactEmail"],
#                         CompanyModel.id != company.id,
#                     )
#                     .first()
#                 )
#                 if exists:
#                     raise HTTPException(
#                         status_code=status.HTTP_409_CONFLICT,
#                         detail="Email already registered with another company",
#                     )
#                 company.contact_email = ci["contactEmail"]

#         # Document Info update
#         if "documentInfo" in data:
#             di = data["documentInfo"]

#             if "logoUrl" in di:
#                 company.logo_url = di["logoUrl"]

#             if "documents" in di:
#                 db.query(CompanyDocumentModel).filter(
#                     CompanyDocumentModel.company_id == company.id
#                 ).delete(synchronize_session=False)

#                 for doc in di["documents"]:
#                     db.add(
#                         CompanyDocumentModel(
#                             company_id=company.id,
#                             document_type=doc.get("documentType"),
#                             document_url=doc.get("documentUrl"),
#                         )
#                     )

#         db.flush()
#         return company

#     except HTTPException:
#         raise
#     except Exception as e:
#         print("DB ERROR 👉", e)  # or logger.exception(e)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Error updating contact info",
#         )


# -----------------------End Update Company Profile Service----------------------- #

# -----------------------Get Terms and Conditions Service----------------------- #
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-1",
)

objects = s3_client.list_objects_v2(
    Bucket="workforce360-s3-bucket", Prefix="company_docs/"
)

print(objects)


import os
import boto3
from botocore.exceptions import ClientError


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1",
    )


def list_company_docs():
    try:
        s3_client = get_s3_client()

        objects = s3_client.list_objects_v2(
            Bucket="workforce360-s3-bucket", Prefix="company_docs/"
        )

        return objects

    except ClientError as e:
        print("S3 Error:", e)
        return None


BUCKET_NAME = "workforce360-s3-bucket"
TERMS_KEY = "workforce_terms.html"  # latest pointer


def get_terms_and_conditions() -> str:
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=TERMS_KEY,
        )

        html_content = response["Body"].read().decode("utf-8")
        return html_content

    except ClientError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to fetch Terms and Conditions",
        )


# -----------------------End Get Terms and Conditions Service----------------------- #


# -----------------------Generate S3 Upload URL Service----------------------- #
def generate_upload_url_service(
    file_type: str,
    current_user,
) -> dict:
    try:
        allowed_types = ["png", "jpg", "jpeg", "pdf"]
        if file_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type",
            )

        CONTENT_TYPES = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "pdf": "application/pdf",
        }

        key = f"company_docs/{current_user}/{uuid4()}.{file_type}"

        url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": "workforce360-s3-bucket",
                "Key": key,
                "ContentType": CONTENT_TYPES[file_type],
            },
            ExpiresIn=300,  # 5 minutes
        )

        return {
            "upload_url": url,
            "file_url": f"https://workforce360-s3-bucket.s3.amazonaws.com/{key}",
        }

    except HTTPException:
        raise
    except Exception as e:
        print("S3 ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating upload URL",
        )


# -----------------------End Generate S3 Upload URL Service----------------------- #


# -----------------------Save Document Service----------------------- #
# def save_document_service(
#     payload: CompanyDocumentCreateSchema,
#     current_user: str,
#     db: Session,
# ) -> CompanyDocumentModel:
#     try:
#         company = (
#             db.query(CompanyModel)
#             .filter(CompanyModel.firebase_uid == current_user)
#             .first()
#         )
#         if not company:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Company profile not found",
#             )

#         document = CompanyDocumentModel(
#             company_id=company.id,
#             document_type=payload.documentType,
#             document_url=payload.documentUrl,
#         )
#         db.add(document)
#         db.flush()
#         return document

#     except Exception as e:
#         print("DB ERROR 👉", e)  # or logger.exception(e)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Error saving document",
#         )


# -----------------------End Save Document Service----------------------- #


# -----------------------Delete Document Service----------------------- #
def delete_document_service(
    document_id: str,
    current_user: str,
    db: Session,
):
    document = (
        db.query(CompanyDocumentModel)
        .join(CompanyModel)
        .filter(
            CompanyDocumentModel.id == document_id,
            CompanyModel.firebase_uid == current_user,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Extract S3 key
    s3_key = document.document_url.split(".com/")[1]

    # Delete from S3
    s3_client.delete_object(
        Bucket="workforce360-s3-bucket",
        Key=s3_key,
    )

    # Delete from DB
    db.delete(document)
    db.flush()


# -----------------------End Delete Document Service----------------------- #


# -----------------------Update Company Address Service----------------------- #
def update_company_address_service(
    address_id: str,
    new_address: CompanyAddressCreateSchema,
    db: Session,
) -> CompanyAddressModel:
    try:
        company_address = (
            db.query(CompanyAddressModel)
            .filter(CompanyAddressModel.id == address_id)
            .first()
        )

        if not company_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company address not found",
            )

        location = from_shape(
            Point(
                new_address.longitude, new_address.latitude
            ),  # IMPORTANT: lng, lat order
            srid=4326,
        )

        # Update fields
        company_address.address = new_address.address
        company_address.unit_name = new_address.unitName
        company_address.city = new_address.city
        company_address.state = new_address.state
        company_address.pincode = new_address.pincode
        company_address.location = location

        db.flush()
        return company_address

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company address",
        )


# -----------------------End Update Company Address Service----------------------- #


# -----------------------Add New Company Service----------------------- #
def add_new_company_service(
    new_address: CompanyAddressCreateSchema,
    firebase_uid: str,
    db: Session,
) -> CompanyModel:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        location = from_shape(
            Point(
                new_address.longitude, new_address.latitude
            ),  # IMPORTANT: lng, lat order
            srid=4326,
        )

        new_company_address = CompanyAddressModel(
            company_id=company.id,
            address=new_address.address,
            unit_name=new_address.unitName,
            city=new_address.city,
            state=new_address.state,
            pincode=new_address.pincode,
            location=location,
        )
        db.add(new_company_address)
        db.flush()
        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding new company address",
        )


# -----------------------End Add New Company Service----------------------- #


# -----------------------Delete Particular Company Address----------------------- #
def delete_company_address_service(
    address_id: str,
    db: Session,
) -> CompanyAddressModel:
    try:
        company_address = (
            db.query(CompanyAddressModel)
            .filter(CompanyAddressModel.id == address_id)
            .first()
        )

        if not company_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company address not found",
            )

        db.delete(company_address)
        db.flush()
        return company_address

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting company address",
        )


# -----------------------End Delete Particular Company Address----------------------- #


# -----------------------Get All Company details Service----------------------- #
def get_all_company_details_service(
    db: Session,
) -> list[CompanyModel]:
    try:
        return db.query(CompanyModel).all()
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching all company details",
        )


# -----------------------End Get All Company details Service----------------------- #


# -----------------------Delete Company Details Service----------------------- #
def delete_company_profile_service(
    phone_number: str,
    db: Session,
) -> CompanyModel:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.auth_phone == phone_number)
            .first()
        )

        db.query(CompanyAddressModel).filter(
            CompanyAddressModel.company_id == company.id
        ).delete()

        db.query(CompanyDocumentModel).filter(
            CompanyDocumentModel.company_id == company.id
        ).delete()

        db.query(CompanyBankDetailsModel).filter(
            CompanyBankDetailsModel.company_id == company.id
        ).delete()

        db.delete(company)
        db.flush()

        return company
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting company details",
        )


# -----------------------End Delete Company Details Service----------------------- #


# -----------------------Get All Address details Service----------------------- #
def get_all_address_details_service(
    db: Session,
) -> list[CompanyAddressModel]:
    try:
        return db.query(CompanyAddressModel).all()
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching all address details",
        )


# -----------------------End Get All Address details Service----------------------- #


# -----------------------Get All Documents details Service----------------------- #
def get_all_documents_details_service(
    db: Session,
) -> list[CompanyDocumentModel]:
    try:
        return db.query(CompanyDocumentModel).all()
    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching all document details",
        )


# -----------------------End Get All Documents details Service----------------------- #


# -----------------------Update Company Profile Details Service----------------------- #
def update_company_profile_details_service(
    firebase_uid: str,
    company_details: CompanyProfileDetailsSchema,
    db: Session,
) -> str:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        company.company_name = company_details.companyName
        company.industry_id = company_details.industryId
        if company_details.gstNo is not None:
            company.gst_number = company_details.gstNo
            company.status = "unapproved"  # Set to unapproved for verification if GST number is updated
            company.status_approval_message_shown = False
        db.flush()
        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company name",
        )


# -----------------------End Update Company Profile Details Service----------------------- #


# -----------------------Create Company Bank Details Service----------------------- #
def create_company_bank_details_service(
    firebase_uid: str,
    bank_details: CompanyBankDetailsSchema,
    db: Session,
) -> str:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        new_company_bank = CompanyBankDetailsModel(
            company_id=company.id,
            bank_name=bank_details.bankName,
            account_holder_name=bank_details.accountHolderName,
            account_number=bank_details.accountNumber,
            ifsc_code=bank_details.ifscCode,
            upi_id=bank_details.upiId,
        )
        db.add(new_company_bank)
        db.flush()

        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating company bank details",
        )


# -----------------------End Create Company Bank Details Service----------------------- #


# -----------------------Update Company Bank Details Service----------------------- #
def update_company_bank_details_service(
    firebase_uid: str,
    bank_details: CompanyBankDetailsSchema,
    db: Session,
) -> str:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        company_bank = (
            db.query(CompanyBankDetailsModel)
            .filter(CompanyBankDetailsModel.company_id == company.id)
            .first()
        )

        if not company_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company bank details not found",
            )

        company_bank.bank_name = bank_details.bankName
        company_bank.account_holder_name = bank_details.accountHolderName
        company_bank.account_number = bank_details.accountNumber
        company_bank.ifsc_code = bank_details.ifscCode
        company_bank.upi_id = bank_details.upiId

        db.flush()
        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company bank details",
        )


# -----------------------End Update Company Bank Details Service----------------------- #


# -----------------------Delete Company Bank Details Service----------------------- #
def delete_company_bank_details_service(
    firebase_uid: str,
    db: Session,
) -> str:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        company_bank = (
            db.query(CompanyBankDetailsModel)
            .filter(CompanyBankDetailsModel.company_id == company.id)
            .first()
        )

        if not company_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company bank details not found",
            )

        db.delete(company_bank)
        db.flush()
        return company_bank

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting company bank details",
        )


# -----------------------End Delete Company Bank Details Service----------------------- #


# -----------------------Get Company Documents based on document type service----------------------- #
def get_company_documents_by_type_service(
    firebase_uid: str,
    document_type: str,
    db: Session,
) -> list[CompanyDocumentModel]:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        documents = (
            db.query(CompanyDocumentModel)
            .filter(
                CompanyDocumentModel.company_id == company.id,
                CompanyDocumentModel.document_type == document_type,
            )
            .all()
        )

        return documents

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching company documents by type",
        )


# -----------------------End Get Company Documents based on document type service----------------------- #


# -----------------------Update Company Logo Service----------------------- #
def update_company_logo_service(
    logoUrl: str,
    firebase_uid: str,
    db: Session,
) -> str:
    try:
        company_profile = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )
        if not company_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        # Update logo URL
        company_profile.logo_url = logoUrl
        db.flush()
        return company_profile

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company logo",
        )


# -----------------------End Update Company Logo Service----------------------- #


# -----------------------Update Company Document info based on document id----------------------- #
def update_document_info_service_by_id(
    document_id: str,
    document_info: CompanyDocumentCreateSchema,
    firebase_uid: str,
    db: Session,
) -> str:
    try:
        document = (
            db.query(CompanyDocumentModel)
            .filter(CompanyDocumentModel.id == document_id)
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company document not found",
            )

        # Update fields
        if document_info.documentType is not None:
            document.document_type = document_info.documentType

        if document_info.documentUrl is not None:
            document.document_url = document_info.documentUrl

        # If document type is IDP is updated, set status to unapproved for verification
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.id == document.company_id)
            .first()
        )
        if company:
            company.status = "unapproved"
            company.status_approval_message_shown = False

        db.flush()
        return document

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company document info",
        )


# -----------------------End Update Company Document info based on document id----------------------- #


# -----------------------Add more documents against company id & document type service----------------------- #
def add_document_against_company_id_and_type_service(
    firebase_uid: str, db: Session, document_info: CompanyDocumentCreateSchema
):
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        document = CompanyDocumentModel(
            document_type=document_info.documentType,
            document_url=document_info.documentUrl,
            company_id=company.id,
        )
        db.add(document)
        # If Any document type is IDP is added, set status to unapproved for verification
        company.status = "unapproved"
        company.status_approval_message_shown = False

        db.flush()
        return document

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding document against company id and type",
        )


# -----------------------End Add more documents against company id & document type service----------------------- #


# -----------------------Get company name and status Service----------------------- #
def company_name_and_status_service(
    firebase_uid: str,
    db: Session,
) -> dict:
    try:
        company = (
            db.query(CompanyModel)
            .filter(CompanyModel.firebase_uid == firebase_uid)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )
        show_approval_message = False
        if company.status == "approved" and not company.status_approval_message_shown:
            show_approval_message = True
            company.status_approval_message_shown = True
            db.flush()
        return {
            "companyId": str(company.id),
            "companyName": company.company_name,
            "logoUrl": company.logo_url,
            "status": company.status,
            # "statusApprovalMessageShown": company.status_approval_message_shown,
            "showApprovalMessage": show_approval_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching company name and status",
        )


# -----------------------End Get company name and status Service----------------------- #


# -----------------------Update Company Status to Approved Service----------------------- #
def update_company_status_to_approved_service(company_id: UUID, db: Session):
    try:
        company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        was_approved = company.status == "approved"
        company.status = "approved"
        if not was_approved:
            company.status_approval_message_shown = False
        db.flush()
        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company status to approved",
        )


# -----------------------End Update Company Status to Approved Service----------------------- #


# -----------------------Update Company Status to Unapproved Service----------------------- #
def update_company_status_to_unapproved_service(company_id: UUID, db: Session):
    try:
        company = db.query(CompanyModel).filter(CompanyModel.id == company_id).first()

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company profile not found",
            )

        was_approved = company.status == "approved"
        company.status = "unapproved"
        if not was_approved:
            company.status_approval_message_shown = False
        db.flush()
        return company

    except HTTPException:
        raise
    except Exception as e:
        print("DB ERROR 👉", e)  # or logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating company status to unapproved",
        )


# -----------------------End Update Company Status to Unapproved Service----------------------- #
