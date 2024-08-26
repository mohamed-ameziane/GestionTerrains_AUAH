from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.conf import settings
from django.http import HttpResponse
from io import BytesIO
from PyPDF2 import PdfMerger
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from .models import *
from .forms import *
import os, json

def format_coordinates(coordinate_str):
    # Remove any existing newline characters
    cleaned_str = coordinate_str.replace('\n', '')
    
    # Convert the cleaned string to a Python list
    try:
        coordinates = json.loads(cleaned_str)
    except json.JSONDecodeError:
        raise ValueError("Invalid coordinate string format.")
    
    # Format each coordinate pair on a new line and enclose in curly braces
    formatted_str = "{\n" + ',\n'.join([f"{coord}" for coord in coordinates]) + "\n}"
    
    return formatted_str


@login_required(redirect_field_name='loginPage', login_url='loginPage')
#----------------------------------------------------------------------------------------------------------------------------------------------
def home(request):
    secteurs_data = ChoixTerrain.objects.values('secteur').annotate(count=Count('choixID'))
    secteurs = [item['secteur'] for item in secteurs_data]
    counts = [item['count'] for item in secteurs_data]

    ref_data = ChoixTerrain.objects.values('refFonciere').annotate(count=Count('choixID'))
    ref_labels = [item['refFonciere'] for item in ref_data]
    ref_counts = [item['count'] for item in ref_data]

    surface_ranges = [
        ('< 100', ChoixTerrain.objects.filter(surface__lt=100).count()),
        ('100-500', ChoixTerrain.objects.filter(surface__gte=100, surface__lt=500).count()),
        ('500-1000', ChoixTerrain.objects.filter(surface__gte=500, surface__lt=1000).count()),
        ('1000+', ChoixTerrain.objects.filter(surface__gte=1000).count()),
    ]
    surface_labels = [label for label, _ in surface_ranges]
    surface_counts = [count for _, count in surface_ranges]

    context = {
        'secteurs': secteurs,
        'counts': counts,
        'ref_labels': ref_labels,
        'ref_counts': ref_counts,
        'surface_labels': surface_labels,
        'surface_counts': surface_counts,
    }

    return render(request, 'base/home.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Utilisateur n\'existe pas')
            return render(request, 'base/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect')
            return render(request, 'base/login.html')

    context = {}
    return render(request, 'base/login.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def logoutView(request):
    logout(request)
    return redirect('loginPage')

#----------------------------------------------------------------------------------------------------------------------------------------------
def message_step(request):
    if request.method == 'POST':
        message_form = MessageForm(request.POST, request.FILES)
        if message_form.is_valid():
            message = message_form.save()
            # Redirect to terrain step, passing the message ref
            return redirect('terrain_step', ref_message=message.refMessage)
    else:
        message_form = MessageForm()

    context = {'message_form': message_form}
    return render(request, 'base/message_step.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def terrain_step(request, ref_message):
    message = get_object_or_404(Message, refMessage=ref_message)

    if request.method == 'POST':
        choix_terrain_form = TerrainForm(request.POST, request.FILES)
        if choix_terrain_form.is_valid():
            choix_terrain = choix_terrain_form.save(commit=False)
            choix_terrain.refMessage = message
            choix_terrain.geo = request.POST.get('coordinates')
            choix_terrain.surface = request.POST.get('area')

            
            choix_terrain.save()
            return redirect('home')
    else:
        choix_terrain_form = TerrainForm()

    context = {'choix_terrain_form': choix_terrain_form, 'message': message}
    return render(request, 'base/terrain_step.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def rapport(request):
    choix_terrains = ChoixTerrain.objects.select_related('refMessage').all()
    
    search_query = {
        'search_choixID': request.GET.get('search_choixID', ''),
        'search_secteur': request.GET.get('search_secteur', ''),
        'min_surface': request.GET.get('min_surface', ''),
        'max_surface': request.GET.get('max_surface', ''),
        'start_date': request.GET.get('start_date', ''),
        'end_date': request.GET.get('end_date', ''),
        'search_refMessage': request.GET.get('search_refMessage', ''),
        'search_objet': request.GET.get('search_objet', ''),
        'search_commune': request.GET.get('search_commune', ''),
        'search_province': request.GET.get('search_province', ''),
        'search_refFonciere': request.GET.get('search_refFonciere', ''),
    }
    
    filters = {}
    
    if 'filter' in request.GET:
        selected_filters = request.GET.getlist('filter')
        
        if 'surface' in selected_filters:
            if search_query['min_surface'] and search_query['max_surface']:
                filters['surface__range'] = (search_query['min_surface'], search_query['max_surface'])
        
        if 'dateChoix' in selected_filters:
            if search_query['start_date'] and search_query['end_date']:
                filters['dateChoix__range'] = (search_query['start_date'], search_query['end_date'])
        
        if 'choixID' in selected_filters:
            filters['choixID'] = search_query['search_choixID']
                
        if 'secteur' in selected_filters:
            filters['secteur'] = search_query['search_secteur']
        
        if 'refMessage' in selected_filters:
            filters['refMessage__refMessage'] = search_query['search_refMessage']
        
        if 'objet' in selected_filters:
            filters['refMessage__objet'] = search_query['search_objet']

        if 'commune' in selected_filters:
            filters['commune'] = search_query['search_commune']

        if 'province' in selected_filters:
            filters['province'] = search_query['search_province']

        if 'refFonciere' in selected_filters:
            filters['refFonciere'] = search_query['search_commune']

    choix_terrains = ChoixTerrain.objects.filter(**filters)
    
    context = {
        'choix_terrains': choix_terrains,
        'search_query': search_query,
    }

    return render(request, 'base/rapport.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def generate_rapport(request, choixID):
    if request.method == 'POST':
        terrain = get_object_or_404(ChoixTerrain, pk=choixID)

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']

        # Create a PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)

        # Create a list to hold the content of the PDF
        elements = []

        # Define images paths
        logo_left_path = os.path.join(settings.BASE_DIR, 'static/images/auah-logo.png')
        logo_right_path = os.path.join(settings.BASE_DIR, 'static/images/ryme.png')

        # Check if the files exist
        if not os.path.isfile(logo_left_path):
            raise FileNotFoundError(f"Logo file not found: {logo_left_path}")
        if not os.path.isfile(logo_right_path):
            raise FileNotFoundError(f"Logo file not found: {logo_right_path}")

        # Add logos
        logo_left = Image(logo_left_path, width=100, height=50)
        logo_right = Image(logo_right_path, width=100, height=50)

        logo_table_data = [
            [logo_left, Paragraph("Rapport de Terrain N° %s" % terrain.choixID, getSampleStyleSheet()['Title']), logo_right]
        ]

        logo_table = Table(logo_table_data, colWidths=[100, 300, 100])
        logo_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('VALIGN', (0, 0), (2, 0), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (2, 0), 10),
        ]))

        elements.append(logo_table)
        elements.append(Paragraph("<br/>", getSampleStyleSheet()['Normal']))

        geo = format_coordinates(terrain.geo)

        # Define table data
        data = [
            ['Field', 'Value'],
            ['Terrain ID', terrain.choixID],
            ['Situation Geographique', Paragraph(geo, normal_style)],
            ['Secteur', terrain.secteur],
            ['Surface', terrain.surface],
            ['Date Choix', terrain.dateChoix],
            ['Reference Message', terrain.refMessage.refMessage],
            ['Date Message', terrain.refMessage.dateMessage],
            ['Object', terrain.refMessage.objet],
            ['Commune', terrain.commune],
            ['Province', terrain.province],
            ['Reference fonciere', terrain.refFonciere],
        ]

        # Create a table and style it
        table = Table(data, colWidths=[200, 400])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSize', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # Add the table to the elements list
        elements.append(table)

        # Build the PDF
        doc.build(elements)

        # Get PDF data from the buffer
        buffer.seek(0)
        report_pdf = buffer.getvalue()
        buffer.close()

        # Path to the folder containing the PDFs
        folder_path = os.path.join('uploads', terrain.refMessage.refMessage)

        # Merge the report PDF with all PDFs in the folder
        merger = PdfMerger()
        report_buffer = BytesIO(report_pdf)
        merger.append(report_buffer)

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.pdf'):
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, 'rb') as f:
                        merger.append(f)

        # Output the merged PDF
        output = BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_{terrain.choixID}.pdf"'
        response.write(output.getvalue())

        return response
    
#----------------------------------------------------------------------------------------------------------------------------------------------
def delete(request, choixID):
    if request.method == 'POST':
        choix_terrain = get_object_or_404(ChoixTerrain, pk=choixID)
        message = choix_terrain.refMessage 
        folder_path = os.path.join('uploads', choix_terrain.refMessage.refMessage)

        # Delete all PDF files in the folder
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        # Delete the folder itself
        if os.path.isdir(folder_path):
            os.rmdir(folder_path)

        # Delete the ChoixTerrain entry
        choix_terrain.delete()

        # Delete the associated Message object
        message.delete()

        messages.success(request, 'La suppression est effectuée avec succès.')
        return redirect('rapport')
    else:
        messages.error(request, 'Méthode de requête invalide.')
        return redirect('rapport')
    

#----------------------------------------------------------------------------------------------------------------------------------------------
def create_commission(request):
    if request.method == 'POST':
        form = CommissionForm(request.POST)
        if form.is_valid():
            ref_message = form.cleaned_data['refMessage']
            cin = form.cleaned_data['participant_cin']
            nom = form.cleaned_data['participant_nom']
            prenom = form.cleaned_data['participant_prenom']
            mail = form.cleaned_data['participant_mail']
            role = form.cleaned_data['participant_role']
            
            participant, created = Participant.objects.get_or_create(cin=cin, defaults={
                'nom': nom,
                'prenom': prenom,
                'mail': mail,
                'role': role
            })
            
            commission, created = Commission.objects.get_or_create(refMessage=ref_message)
            commission.participants.add(participant)
            return redirect('create_commission')
    else:
        form = CommissionForm()
    
    context = {'form': form}
    return render(request, 'base/create_commission.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------
def list_participants(request):
    if request.method == 'POST':
        form = SearchCommissionForm(request.POST)
        if form.is_valid():
            ref_message = form.cleaned_data['refMessage']
            commissions = Commission.objects.filter(refMessage=ref_message).prefetch_related('participants')
            participants = []
            if commissions:
                participants = commissions[0].participants.all()
            return render(request, 'base/list_participants.html', {'form': form, 'participants': participants})
    else:
        form = SearchCommissionForm()
    
    return render(request, 'base/list_participants.html', {'form': form, 'participants': []})