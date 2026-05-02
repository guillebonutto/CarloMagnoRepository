import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from productos.models import Producto

def vincular_imagenes():
    # Mapeo de ID -> Nombre de archivo en Supabase
    # Tomé los nombres más limpios y recientes de tu carpeta
    mapping = {
        24: "product_24_Bk45lxY_450x563.png",
        37: "product_37_KpeKnM2_450x563.png",
        38: "product_38_xomiVNj_450x563.png",
        39: "product_39_lT2xFEj_450x563.png",
        41: "product_41_Dt1IHC2_450x563.png",
        42: "product_42_5e2uGdU_450x563.png",
        47: "product_47_Sa23R7U_450x563.png",
        49: "product_49_NC1NKwj_450x563.png",
        53: "product_53_ijn9Hyt_450x563.png",
        54: "product_54_fA4Soqp_450x563.png",
        55: "product_55_LXJMLXR_450x563.png",
        56: "product_56_v3ILWRe_450x563.png",
        57: "product_57_GIKmEpJ_450x563.png",
        58: "product_58_Or87ht9_450x563.png",
        59: "product_59_qoPS05H_450x563.png",
        60: "product_60_F9T34c9_450x563.png",
        64: "product_64_NTCNJg4_450x563.png",
        65: "product_65_y68pSmm_450x563.png",
        67: "product_67_rKtjmNW_450x563.png",
        68: "product_68_d7cia1R_450x563.png",
        69: "product_69_6ZnKwRQ_450x563.png",
        70: "product_70_3ILYTod_450x563.png",
        71: "product_71_eLgj7Tq_450x563.png",
        74: "product_74_zdwNLdp_450x563.png",
        75: "product_75_NQaMl1X_450x563.png",
        78: "product_78_88JkH3x_450x563.png",
        79: "product_79_11VZed8_450x563.png",
        81: "product_81_b2QuRJD_450x563.png",
        82: "product_82_Fbjg78d_450x563.png",
        83: "product_83_2UTvOKu_450x563.png",
        89: "product_89_hjzohRG_450x563.png",
        91: "product_91_uXiudfD_450x563.png",
        92: "product_92_tclBOTD_450x563.png",
        93: "product_93_1S5nFFJ_450x563.png",
        95: "product_95_mrDl5JC_450x563.png",
        98: "product_98_DBx7wtV_450x563.png",
        100: "product_100_bSlXByB_450x563.png",
        102: "product_102_x6rEC5w_450x563.png",
        103: "product_103_OKsm7W1_450x563.png",
        104: "product_104_CztCLfP_450x563.png",
        108: "product_108_hp3FUWt_450x563.png",
        110: "product_110_O8u512i_450x563.png",
        113: "product_113_6faOZQi_450x563.png",
        115: "product_115_Iq4bbNu_450x563.png",
        116: "product_116_T5Lwxr9_450x563.png",
        117: "product_117_Y7AaLbd_450x563.png",
        118: "product_118_Fmzf149_450x563.png",
        119: "product_119_Rz4a5dQ_450x563.png",
        120: "manual_120_450x563.png",
        121: "manual_121_450x563.png",
        125: "product_125_dEiFqhO_450x563.png",
        127: "product_127_ycvyVAL_450x563.png",
        128: "product_128_LSYpNYR_450x563.png",
        134: "product_134_UuvT9c0_450x563.png",
        141: "product_141_zKkZqaU_450x563.png",
        143: "product_143_LeQwgEa_450x563.png",
        146: "product_146_7tttI1c_450x563.png",
        147: "product_147_wZZYv8B_450x563.png",
        148: "product_148_yiI0n6r_450x563.png",
        150: "product_150_ke7AvEb_450x563.png",
        151: "product_151_6bkZEld_450x563.png",
        152: "manual_152_450x563.png",
        153: "product_153_wXJUZwB_450x563.png",
        155: "product_155_ga9N7N6_450x563.png",
    }

    print("Iniciando vinculación de imágenes...")
    
    count = 0
    for prod_id, filename in mapping.items():
        # Django Supabase Storage guarda con el prefijo de la carpeta del bucket
        # Si las subiste a la raíz del bucket 'productos', el path es solo el nombre
        # Si Django las maneja, suele guardarlas como 'nombre_archivo'
        try:
            p = Producto.objects.filter(id=prod_id).first()
            if p:
                p.imagen = filename
                p.save()
                print(f"Vinculado: {p.nombre} -> {filename}")
                count += 1
        except Exception as e:
            print(f"Error vinculando ID {prod_id}: {e}")

    print(f"Vinculación finalizada. {count} productos actualizados.")

if __name__ == "__main__":
    vincular_imagenes()
