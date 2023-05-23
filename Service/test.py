import matplotlib.pyplot as plt
def generate_relation_image(application_id, data):
    application = None
    for item in data:
        if item["applicationSrc"]["id"] == application_id or item["applicationTarget"]["id"] == application_id:
            application = item
            break

    if application is None:
        return None  

    applications = set()
    for item in data:
        applications.add(item["applicationSrc"]["appName"])
        applications.add(item["applicationTarget"]["appName"])

    positions = {}
    angle = 0
    angle_increment = 2 * 3.14159 / len(applications)

    for app in applications:
        x = 0.5 + 0.4 * (angle / (2 * 3.14159))
        y = 0.5 + 0.4 * (angle / (2 * 3.14159))
        positions[app] = (x, y)
        angle += angle_increment

    fig, ax = plt.subplots()

    for item in data:
        src_app = item["applicationSrc"]["appName"]
        target_app = item["applicationTarget"]["appName"]
        src_pos = positions[src_app]
        target_pos = positions[target_app]

        if item["flow"] == "INTERNAL":
            arrow_color = 'green'
        else:
            arrow_color = 'red'

        ax.arrow(src_pos[0], src_pos[1], target_pos[0] - src_pos[0], target_pos[1] - src_pos[1], color=arrow_color, head_width=0.02)

    for app, pos in positions.items():
        circle = plt.Circle(pos, 0.05, color='orange')
        ax.add_artist(circle)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.axis('off')  

    image_path = f'relations_{application_id}.png'
    plt.savefig(image_path)

    return image_path