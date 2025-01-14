from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import EncryptedImage, Profile
from .forms import SignUpForm, ImageUploadForm
from .encryption_utils import generate_aes_key_iv, encrypt_with_aes, encrypt_with_rsa
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
            return redirect('profile')
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
            return redirect('profile')
    return render(request, 'transfer/login.html')
    
@login_required
def profile(request):
    images = []
    private_key_pem = request.user.profile.private_key.encode()  # Ensure the user has a private key

    for image in EncryptedImage.objects.filter(receiver=request.user):
        try:
            decrypted_image = image.decrypt_image(private_key_pem)  # Decrypt the image
            images.append({
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
                return redirect('profile')
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

