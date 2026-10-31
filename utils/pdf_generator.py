import os
from io import BytesIO
import logging
from django.conf import settings
from django.http import HttpResponse
from django.contrib.staticfiles import finders
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


def link_callback(uri, rel):
    """
    Converts HTML image URIs to absolute system paths so xhtml2pdf can access static and media files.
    """
    # 1. Check if uri is already an absolute system path on disk
    if os.path.isabs(uri) and os.path.isfile(uri):
        return uri

    # 2. Strip domain if full URL was passed (e.g. http://127.0.0.1:8000/media/...)
    if uri.startswith("http://") or uri.startswith("https://"):
        uri = "/" + uri.split("/", 3)[-1]

    # 3. Handle Media files (e.g., student passport photos)
    if uri.startswith(settings.MEDIA_URL):
        relative_media = uri.replace(settings.MEDIA_URL, "", 1)
        path = os.path.join(settings.MEDIA_ROOT, relative_media)
        if os.path.isfile(path):
            return path

    # 4. Handle Static files (e.g., school logo)
    if uri.startswith(settings.STATIC_URL):
        relative_static = uri.replace(settings.STATIC_URL, "", 1)
        path = finders.find(relative_static)
        if path:
            if isinstance(path, (list, tuple)):
                path = path[0]
            if os.path.isfile(path):
                return path

    # 5. Fallback for raw static search
    result = finders.find(uri)
    if result:
        if isinstance(result, (list, tuple)):
            result = result[0]
        if os.path.isfile(result):
            return result

    return uri


def render_html_to_pdf(html_string: str) -> bytes:
    """
    Renders an HTML string into PDF bytes using xhtml2pdf with local path resolution.
    """
    result = BytesIO()
    pdf_status = pisa.CreatePDF(
        src=html_string, 
        dest=result, 
        link_callback=link_callback
    )
    
    if pdf_status.err:
        logger.error(f"xhtml2pdf rendering error count: {pdf_status.err}")
        raise ValueError(f"Error generating PDF: {pdf_status.err} errors encountered.")
    
    return result.getvalue()


def pdf_file_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    """
    Wraps PDF bytes into an inline HTTP response suitable for viewing/downloading in browser.
    """
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response