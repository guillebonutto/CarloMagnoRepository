import base64
import json
import urllib.request
import urllib.error
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Producto

@csrf_exempt
def vton_generate(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_image_b64 = data.get("user_image")
            producto_id = data.get("producto_id")
            
            if not user_image_b64 or not producto_id:
                return JsonResponse({"success": False, "message": "Faltan datos de imagen o producto"})
                
            producto = get_object_or_404(Producto, id=producto_id)
            if not producto.imagen:
                return JsonResponse({"success": False, "message": "El producto no tiene imagen para probar"})
                
            api_token = getattr(settings, "WAVESPEED_API_TOKEN", "")
            if not api_token:
                return JsonResponse({"success": False, "message": "API Token de Wavespeed no configurado en settings.py"})

            # Convertir la imagen del producto local a Base64
            try:
                with open(producto.imagen.path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    ext = producto.imagen.path.split('.')[-1].lower()
                    mime_type = "image/png" if ext == "png" else "image/jpeg"
                    garment_b64 = f"data:{mime_type};base64,{encoded_string}"
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Error leyendo la imagen del producto: {str(e)}"})
            
            # URL y headers para Wavespeed API
            url = 'https://api.wavespeed.ai/api/v3/wavespeed-ai/ai-clothes-changer'
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = json.dumps({
                "image": user_image_b64,
                "clothes_images": [garment_b64]
            }).encode('utf-8')
            
            # Realizar petición POST
            req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            output_url = None
            
            # Revisar si Wavespeed nos dio la URL de status ("urls" -> "get")
            data_obj = result.get("data", {})
            get_url = data_obj.get("urls", {}).get("get")
            
            if get_url:
                # Iniciar Polling (esperar a que la imagen se genere)
                for _ in range(60): # Esperar hasta 120 segundos
                    time.sleep(2)
                    req_status = urllib.request.Request(get_url, headers=headers)
                    with urllib.request.urlopen(req_status) as res_status:
                        poll_res = json.loads(res_status.read().decode('utf-8'))
                        poll_data = poll_res.get("data", {})
                        status = poll_data.get("status")
                        
                        if status == "succeeded" or status == "completed" or status == "success":
                            # Buscar el output (normalmente en outputs[0] o output)
                            outputs = poll_data.get("outputs", [])
                            if outputs and isinstance(outputs, list) and len(outputs) > 0:
                                output_url = outputs[0]
                            else:
                                output_url = poll_data.get("output")
                            break
                        elif status in ["failed", "error", "canceled"]:
                            break
            
            if output_url:
                return JsonResponse({"success": True, "result_url": output_url})
            else:
                return JsonResponse({"success": False, "message": f"Respuesta inesperada de la IA: {json.dumps(result)}"})
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return JsonResponse({"success": False, "message": f"Error HTTP {e.code}: {error_body}"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
            
    return JsonResponse({"success": False, "message": "Método no permitido"})
