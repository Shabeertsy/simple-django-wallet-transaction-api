from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer ,WalletSerializer,TransactionSerializer
from django.shortcuts import get_object_or_404
from .models import User,Wallet,Transactions
from rest_framework import status
from django.utils import timezone



# Create your views here.
## user register ##
@api_view(['POST'])
def register_user(request):
    phone=request.data.get('phone_number')
    if User.objects.filter(phone_number=phone).exists():
        return Response('phone number is exists')
    else:
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
## create a  wallet ##
@api_view(['POST'])
def create_wallet(request, id):
    phone = request.data.get('phone_number')
    user = get_object_or_404(User, pk=id)

    if user.phone_number == phone and not Wallet.objects.filter(phone_number=phone):
        serializer = WalletSerializer(data=request.data, partial=True)
        serializer.user = user
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"message": "Wallet created successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"message": "wallet with this number is already exists"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def send_money(request,id):
    phone = request.data.get('reciver_phone_number')
    amount = float(request.data.get('amount'))
    sender_phone=get_object_or_404(User,pk=id).phone_number

    try:
        rec_wallet = Wallet.objects.get(phone_number=phone)
        send_wallet = Wallet.objects.get(phone_number=sender_phone)
    except Wallet.DoesNotExist:
        return Response({"message": "No account found with the provided phone number"}, status=status.HTTP_400_BAD_REQUEST)
    except Wallet.MultipleObjectsReturned:
        return Response({"message": "Multiple accounts found with the provided phone number"}, status=status.HTTP_400_BAD_REQUEST)
    if phone != sender_phone:
        if send_wallet.balance >= amount:
            rec_wallet.balance += amount
            rec_wallet.save()
            send_wallet.balance -= amount
            send_wallet.save()

            transaction = Transactions.objects.create(
                wallet=send_wallet,
                sender_phone=send_wallet.phone_number,
                receiver_phone=rec_wallet.phone_number,
                amount=amount,
                date_time=timezone.now()
            )
            serializer=TransactionSerializer(transaction)
            return Response({"data":serializer.data,"message": "amount transfer succesfully"}, status=status.HTTP_201_CREATED)
        return Response({"message": "insufficient balance"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "not allow same phone number"}, status=status.HTTP_400_BAD_REQUEST)
    

## for bank ##
@api_view(['POST'])
def add_money(request,wallet_id):
        amount=int(request.data.get('amount'))
        wallet=get_object_or_404(Wallet,pk=wallet_id)
        wallet+=amount
        wallet.save()
        return Response({"amount added succussfully"})


@api_view(['GET'])
def transactions(request,id):
        user=get_object_or_404(User,pk=id)
        wallet=get_object_or_404(Wallet,user=user)
        data=Transactions.objects.filter(wallet=wallet)
        serializer=TransactionSerializer(data,many=True)
        return Response(serializer.data)
