from django.http import JsonResponse

def Response(result, message, data=None, status=200):
    response = {
        "status" : result,
        "message" : message
    }
    if data:
        response["data"] = data
    return JsonResponse(response, status=status)