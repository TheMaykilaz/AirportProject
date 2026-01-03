from django.views.generic import TemplateView
from django.conf import settings
import os

class ReactAppView(TemplateView):
    """
    Serves the compiled React app.
    In production, this view serves the React app built files.
    """
    template_name = 'react_app.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if React build exists
        react_build_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'react', 'index.html')
        context['react_built'] = os.path.exists(react_build_path)
        return context

