from .utils import render_template_with_nav_info
from .. import main


@main.route('/')
def index():
    return render_template_with_nav_info('main/index.html')