class Page:

	def __init__(self,
				date,
				url,
				status_code,
				title,
				meta_desc,
				canonical,
				canon_match,
				h1,
				h2):
		self.date = date
		self.url = url
		self.status_code = status_code
		self.title = title
		self.meta_desc = meta_desc
		self.canonical = canonical
		self.canon_match = canon_match
		self.h1 = h1
		self.h2 = h2