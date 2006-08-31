import pprint

from zookeepr.model import Proposal, ProposalType, Person
from zookeepr.tests.functional import *

class TestProposalBase(object):
    """Base class that sets up proposal objects for experimenting with.
    """
    def setUp(self):
        super(TestProposalBase, self).setUp()
        
        self.proposal1 = model.Proposal(title='proposal1')
        self.proposal2 = model.Proposal(title='proposal2')
        self.objectstore.save(self.proposal1)
        self.objectstore.save(self.proposal2)
        self.objectstore.flush()

    def tearDown(self):
        self.objectstore.delete(self.proposal2)
        self.objectstore.delete(self.proposal1)
        self.objectstore.flush()
        
        super(TestProposalBase, self).tearDown()

class TestProposal(SignedInControllerTest):
    model = Proposal
    name = 'proposal'
    url = '/proposal'
    samples = [dict(title='test',
                    abstract='abstract 1',
                    experience='experience 1',
                    url='http://example.org',
                    attachment=buffer('foo'),
                    ),
               dict(title='not a test',
                    abstract='abstract 2',
                    experience='experience 2',
                    url='http://lca2007.linux.org.au',
                    attachment=buffer('bar'),
                    ),
               ]

    def additional(self, obj):
        obj.people.append(self.person)
        obj.type = self.objectstore.get(ProposalType, 1)
        return obj
    
    def setUp(self):
        super(TestProposal, self).setUp()
        model.proposal.tables.proposal_type.insert().execute(
            dict(id=1, name='Paper'),
            )
        model.proposal.tables.proposal_type.insert().execute(
            dict(id=2, name='Presentation'),
            )
        model.proposal.tables.proposal_type.insert().execute(
            dict(id=3, name='Miniconf'),
            )

    def tearDown(self):
        model.proposal.tables.proposal_type.delete().execute()
        super(TestProposal, self).tearDown()

    def test_selected_radio_button_in_edit(self):
        # Test that a radio button is checked when editing a proposal
        s = Proposal(id=1,
                       type=self.objectstore.get(ProposalType, 3),
                       title='foo',
                       abstract='bar',
                       experience='',
                       url='')
        self.objectstore.save(s)
        
        self.person.proposals.append(s)
        
        self.objectstore.flush()

        resp = self.app.get(url_for(controller='proposal',
                                    action='edit',
                                    id=s.id))

        print resp.session

        f = resp.form

        print "response:"
        print resp
        print "f.fields:"
        pprint.pprint(f.fields)

        # the value being returned is a string, from the form defaults
        self.assertEqual('3', f.fields['proposal.type'][0].value)

        # clean up
        self.objectstore.delete(s)
        self.objectstore.flush()


    def test_proposal_view_lockdown(self):
        # we got one person already with login
        # create a sceond
        p2 = Person(email_address='test2@example.org',
                    password='test')
        self.objectstore.save(p2)
        # create a proposal
        s = Proposal(title='foo')
        self.objectstore.save(s)
        p2.proposals.append(s)
        self.objectstore.flush()
        # try to view the proposal as the other person
        resp = self.app.get(url_for(controller='proposal',
                                    action='view',
                                    id=s.id),
                            status=403)

        # clean up
        self.objectstore.delete(p2)
        self.objectstore.delete(s)
        self.objectstore.flush()


    def test_proposal_edit_lockdown(self):
        # we got one person already with login
        # create a sceond
        p2 = Person(email_address='test2@example.org',
                    password='test')
        self.objectstore.save(p2)
        # create a proposal
        s = Proposal(title='foo')
        self.objectstore.save(s)
        p2.proposals.append(s)
        self.objectstore.flush()
        # try to view the proposal as the other person
        resp = self.app.get(url_for(controller='proposal',
                                    action='edit',
                                    id=s.id),
                            status=403)

        # also try to post to it
        resp = self.app.post(url_for(controller='proposal',
                                     action='edit',
                                     id=s.id),
                             params={},
                             status=403)

        # clean up
        self.objectstore.delete(p2)
        self.objectstore.delete(s)
        self.objectstore.flush()


    def test_proposal_delete_lockdown(self):
        # we got one person already with login
        # create a sceond
        p2 = Person(email_address='test2@example.org',
                    password='test')
        self.objectstore.save(p2)
        self.objectstore.flush()
        # create a proposal
        s = Proposal(title='foo')
        self.objectstore.save(s)
        p2.proposals.append(s)
        self.objectstore.flush()
        # try to view the proposal as the other person
        resp = self.app.get(url_for(controller='proposal',
                                    action='delete',
                                    id=s.id),
                            status=403)

        # also try to post to it
        resp = self.app.post(url_for(controller='proposal',
                                     action='delete',
                                     id=s.id),
                             params={},
                             status=403)

        # clean up
        self.objectstore.delete(p2)
        self.objectstore.delete(s)
        self.objectstore.flush()


    def test_proposal_list_lockdown(self):
        # we got one person already with login
        # create a sceond
        p2 = Person(email_address='test2@example.org',
                    password='test')
        self.objectstore.save(p2)
        # create a proposal
        s = Proposal(title='foo')
        self.objectstore.save(s)
        p2.proposals.append(s)
        self.objectstore.flush()
        # try to view the proposal as the other person
        resp = self.app.get(url_for(controller='proposal',
                                    action='index'),
                            status=403)

        # clean up
        self.objectstore.delete(p2)
        self.objectstore.delete(s)
        self.objectstore.flush()


    def test_submit_another(self):
        # created guy with login
        # and a proposal
        s1 = Proposal(title='sub one')
        self.objectstore.save(s1)
        self.objectstore.flush()

        # now go home, click on the submit another link, and do so
        resp = self.app.get('/')
        print resp
        resp = resp.click(description='submit another')
        #print resp
        f = resp.form
        f['proposal.title'] = 'sub two'
        f['proposal.type'] = 1
        f['proposal.abstract'] = "cubist"
        f['proposal.experience'] = "n"
        f['proposal.attachment'] = buffer("foo")
        print f.submit_fields()
        resp = f.submit()
        resp = resp.follow()

        # does it exist?
        subs = self.objectstore.query(Proposal).select_by(title='sub two')
        self.assertEqual(1, len(subs))

        s2 = subs[0]
        # is it attached to our guy?
        self.failUnless(s2 in self.person.proposals, "s2 not in p.proposals (currently %r)" % self.person.proposals)
        
        # clean up
        self.objectstore.delete(s2)
        self.objectstore.delete(s1)
        self.objectstore.flush()

    def test_proposal_list(self):
        # we're logged in but still can't see it
        resp = self.app.get(url_for(controller='proposal',
                                    action='index'),
                            status=403)

    def test_proposal_list_reviewer(self):
        # we're logged in and we're a reviewer
        r = model.Role('reviewer')
        self.person.roles.append(r)
        self.objectstore.save(r)
        self.objectstore.flush()

        resp = self.app.get(url_for(controller='proposal',
                                    action='index'))


        # clean up
        self.objectstore.delete(r)
        self.objectstore.flush()

    def test_proposal_view(self):
        model.proposal.tables.proposal.insert().execute(
            dict(id=37, title='test view',
                 proposal_type_id=1)
            )
        p = self.objectstore.get(Proposal, 37)
        pid = p.id
        
        # we're logged in but this isn't our proposal
        # should 403
        resp = self.app.get(url_for(controller='proposal',
                                    action='view',
                                    id=p.id),
                            status=403)
                            
        # clean up
        self.objectstore.delete(self.objectstore.get(Proposal, pid))
        self.objectstore.flush()

    def test_proposal_view(self):
        model.proposal.tables.proposal.insert().execute(
            dict(id=37, title='test view',
                 proposal_type_id=1)
            )
        p = self.objectstore.get(Proposal, 37)
        self.person.proposals.append(p)
        self.objectstore.flush()
        
        # we're logged in and this is ours
        resp = self.app.get(url_for(controller='proposal',
                                    action='view',
                                    id=p.id))
                            
        # clean up
        self.objectstore.delete(p)
        self.objectstore.flush()
