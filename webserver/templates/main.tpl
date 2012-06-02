%if name == 'Guest':
	<h1>You are currently a {{name}}.</h1>
	<p><a href="/register">Create</a> an account.</p>
%else:
	<h1>Hello {{name.title()}}!</h1>
%end
%rebase base title='SMS Signup - Home', root=root
