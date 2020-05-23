from models import measure
import time
def infr_data_to_md(sqlres:list):
    """Generates a markdown table from infraction data
        
        Parameters:
        sqlres: SQL result
    """
    
    # Initalize an empty string
    md = ""

    # Check if there are any infractions
    if(len(sqlres) < 1):
        md = "No infractions"

    for inf in sqlres:
        md = f"""{md}
        `{inf[0][:8]}` • **{str(measure.Measure(inf[2]))}** • {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(int(inf[5])))} • {inf[3]}
        """
    return md
