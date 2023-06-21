class ProgressBar:
    def __init__(self, length=8, filled_emoji='🟪', empty_emoji='▫'):
        self.length = length
        self.filled_emoji = filled_emoji
        self.empty_emoji = empty_emoji

    def create_progress_bar(self, progress):
        filled_length = int(progress / 100 * self.length)
        remaining_length = self.length - filled_length

        filled_emojis = self.filled_emoji * filled_length
        remaining_emojis = self.empty_emoji * remaining_length

        progress_bar = f'[{filled_emojis}{remaining_emojis}]'
        return progress_bar

    def show_progress(self, progress):
        percentage = f'{progress}%'
        progress_bar = self.create_progress_bar(progress)
        return f'{progress_bar} {percentage}'