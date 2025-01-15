from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import EncryptedImage, Profile
from .forms import SignUpForm, ImageUploadForm
from .encryption_utils import generate_aes_key_iv, encrypt_with_aes, encrypt_with_rsa
#for image classification
from django.http import JsonResponse
import base64
from PIL import Image
from io import BytesIO
import torch
from torchvision import transforms as T
import timm
# from .models import User, Profile

def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = Profile.objects.create(user=user)
            profile.generate_key_pair()  # Generate public/private keys
            profile.save()
            login(request, user)
            return redirect('transfer:profile')
    else:
        form = SignUpForm()
    return render(request, 'transfer/sign_up.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('transfer:profile')
    return render(request, 'transfer/login.html')
    
@login_required
def profile(request):
    images = []
    private_key_pem = request.user.profile.private_key.encode()  # Ensure the user has a private key

    for image in EncryptedImage.objects.filter(receiver=request.user):
        try:
            decrypted_image = image.decrypt_image(private_key_pem)  # Decrypt the image
            images.append({
                'id': image.id,  # Include the image ID
                'sender': image.sender.username,
                'image': decrypted_image
            })
        except Exception as e:
            print(f"Decryption failed: {e}")
            continue

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = request.FILES['image']
            receiver_username = form.cleaned_data['receiver']

            try:
                receiver = User.objects.get(username=receiver_username)
                receiver_profile = Profile.objects.get(user=receiver)

                if not receiver_profile.public_key:
                    return render(request, 'transfer/profile.html', {
                        'images': images,
                        'form': form,
                        'error': 'Receiver does not have a public key'
                    })

                aes_key, iv = generate_aes_key_iv()
                encrypted_image = encrypt_with_aes(aes_key, iv, image.read())
                encrypted_key = encrypt_with_rsa(
                    receiver_profile.public_key.encode(), aes_key + iv
                )

                EncryptedImage.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    encrypted_image=encrypted_image,
                    encrypted_key=encrypted_key
                )
                return redirect('transfer:profile')
            except User.DoesNotExist:
                return render(request, 'transfer/profile.html', {
                    'images': images,
                    'form': form,
                    'error': 'Receiver not found'
                })
    else:
        form = ImageUploadForm()

    return render(request, 'transfer/profile.html', {'images': images, 'form': form})

def home(request):
    return render(request, 'transfer/home.html')

#for model import
# Load your model once globally
model = torch.load('models/vit_complete_model.pth')
model.eval()
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)

# Define the image transformation
transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(timm.data.IMAGENET_DEFAULT_MEAN, timm.data.IMAGENET_DEFAULT_STD)
])

# Define the list of classes
classes = ['glioma', 'meningioma', 'notumor', 'pituitary']  # Replace with actual class names
@login_required
def predict_image_view(request):
    if request.method == 'POST':
        image_id = request.POST.get('image_id')
        if not image_id:
            return JsonResponse({'error': 'Image ID is missing'}, status=400)
        try:
            image_obj = EncryptedImage.objects.get(id=image_id, receiver=request.user)
            decrypted_image_data = image_obj.decrypt_image(request.user.profile.private_key.encode())

            try:
                image = Image.open(BytesIO(decrypted_image_data)).convert('RGB')
            except Exception as e:
                print(f"Image loading failed: {e}")
                return JsonResponse({'error': 'Unable to process image'}, status=400)

            image = transform(image).unsqueeze(0).to(device)

            with torch.no_grad():
                outputs = model(image)
                _, predicted = torch.max(outputs.logits, 1)

            prediction_result = classes[predicted.item()]
            print(f"Prediction for Image ID {image_id}: {prediction_result}")  # Print prediction to console

            # Save prediction in the database
            image_obj.prediction = prediction_result
            image_obj.save()

            return redirect('transfer:profile')
        except EncryptedImage.DoesNotExist:
            return JsonResponse({'error': 'Image not found or you do not have permission'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# @login_required
# def predict_image_view(request):
#     if request.method == 'POST':
#         image_id = request.POST.get('image_id')
#         if not image_id:
#             return JsonResponse({'error': 'Image ID is missing'}, status=400)
#         try:
#             image_obj = EncryptedImage.objects.get(id=image_id, receiver=request.user)
#             decrypted_image_data = base64.b64decode(image_obj.encrypted_image)  # Assuming the image is in base64 format
            
#             # Convert bytes to PIL Image
#             image = Image.open(BytesIO(decrypted_image_data)).convert('RGB')
#             image = transform(image).unsqueeze(0).to(device)

#             with torch.no_grad():
#                 outputs = model(image)
#                 _, predicted = torch.max(outputs.logits, 1)

#             # Save prediction in the database
#             image_obj.prediction = classes[predicted.item()]
#             image_obj.save()

#             return redirect('transfer:profile')  # Redirect back to profile
#         except EncryptedImage.DoesNotExist:
#             return JsonResponse({'error': 'Image not found or you do not have permission'}, status=404)

#     return JsonResponse({'error': 'Invalid request'}, status=400)




























# @login_required
# def profile(request):
#     images = EncryptedImage.objects.filter(receiver=request.user)

#     if request.method == 'POST':
#         form = ImageUploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             image = request.FILES['image']
#             receiver_username = form.cleaned_data['receiver']

#             try:
#                 receiver = User.objects.get(username=receiver_username)
#                 receiver_profile = Profile.objects.get(user=receiver)

#                 if not receiver_profile.public_key:
#                     return render(request, 'transfer/profile.html', {
#                         'images': images,
#                         'form': form,
#                         'error': 'Receiver does not have a public key'
#                     })

#                 aes_key, iv = generate_aes_key_iv()
#                 encrypted_image = encrypt_with_aes(aes_key, iv, image.read())
#                 encrypted_key = encrypt_with_rsa(
#                     receiver_profile.public_key.encode(), aes_key + iv
#                 )

#                 EncryptedImage.objects.create(
#                     sender=request.user,
#                     receiver=receiver,
#                     encrypted_image=encrypted_image,
#                     encrypted_key=encrypted_key
#                 )
#                 return redirect('profile')
#             except User.DoesNotExist:
#                 return render(request, 'transfer/profile.html', {'images': images, 'form': form, 'error': 'Receiver not found'})
#     else:
#         form = ImageUploadForm()

#     return render(request, 'transfer/profile.html', {'images': images, 'form': form})

